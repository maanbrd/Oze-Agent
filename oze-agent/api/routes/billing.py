"""Internal billing routes called by trusted web infrastructure."""

from __future__ import annotations

import hashlib
import hmac
import json
import logging
import time
from datetime import datetime, timezone
from typing import Annotated, Any

from fastapi import APIRouter, Header, HTTPException, Request, status

from bot.config import Config
from shared.database import get_supabase_client

logger = logging.getLogger(__name__)
router = APIRouter()

MAX_SIGNATURE_AGE_SECONDS = 300
ACTIVE_STRIPE_STATUSES = {"active", "trialing"}
PAST_DUE_STRIPE_STATUSES = {"past_due", "unpaid", "incomplete"}


def _expected_signature(raw_body: bytes, timestamp: str, secret: str) -> str:
    signed_payload = timestamp.encode("utf-8") + b"." + raw_body
    digest = hmac.new(secret.encode("utf-8"), signed_payload, hashlib.sha256).hexdigest()
    return f"sha256={digest}"


def verify_internal_signature(
    raw_body: bytes,
    timestamp: str | None,
    signature: str | None,
    now: int | None = None,
) -> None:
    """Verify Vercel -> FastAPI HMAC over the exact JSON body."""
    secret = Config.BILLING_INTERNAL_SECRET
    if not secret:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Billing internal secret is not configured.",
        )

    if not timestamp or not signature:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing billing signature headers.",
        )

    try:
        timestamp_int = int(timestamp)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid billing timestamp.",
        ) from exc

    current_time = int(time.time()) if now is None else now
    if abs(current_time - timestamp_int) > MAX_SIGNATURE_AGE_SECONDS:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Stale billing signature.",
        )

    expected = _expected_signature(raw_body, timestamp, secret)
    if not hmac.compare_digest(expected, signature):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid billing signature.",
        )


def _iso_from_stripe_timestamp(value: Any) -> str | None:
    if not isinstance(value, int):
        return None
    return datetime.fromtimestamp(value, tz=timezone.utc).isoformat()


def _coerce_money_pln(cents: Any) -> float:
    if not isinstance(cents, int):
        return 0.0
    return round(cents / 100, 2)


def _subscription_status(stripe_status: str | None, deleted: bool = False) -> str:
    if deleted or stripe_status == "canceled":
        return "expired"
    if stripe_status in ACTIVE_STRIPE_STATUSES:
        return "active"
    if stripe_status in PAST_DUE_STRIPE_STATUSES:
        return "past_due"
    return "pending_payment"


def _metadata_user_id(stripe_object: dict[str, Any]) -> str | None:
    for metadata in _metadata_sources(stripe_object):
        user_id = metadata.get("user_id")
        if isinstance(user_id, str) and user_id:
            return user_id
    return None


def _metadata_plan(stripe_object: dict[str, Any]) -> str | None:
    for metadata in _metadata_sources(stripe_object):
        plan = metadata.get("plan")
        if plan in {"monthly", "yearly"}:
            return plan
    return None


def _stripe_id(value: Any) -> str | None:
    if isinstance(value, str):
        return value
    if isinstance(value, dict) and isinstance(value.get("id"), str):
        return value["id"]
    return None


def _metadata_sources(stripe_object: dict[str, Any]) -> list[dict[str, Any]]:
    sources: list[dict[str, Any]] = []

    metadata = stripe_object.get("metadata")
    if isinstance(metadata, dict):
        sources.append(metadata)

    parent = stripe_object.get("parent")
    if isinstance(parent, dict):
        subscription_details = parent.get("subscription_details")
        if isinstance(subscription_details, dict):
            parent_metadata = subscription_details.get("metadata")
            if isinstance(parent_metadata, dict):
                sources.append(parent_metadata)

    return sources


def _parent_subscription_id(parent: Any) -> str | None:
    if not isinstance(parent, dict):
        return None

    for details_key in (
        "subscription_details",
        "invoice_item_details",
        "subscription_item_details",
    ):
        details = parent.get(details_key)
        if isinstance(details, dict):
            subscription_id = _stripe_id(details.get("subscription"))
            if subscription_id:
                return subscription_id

    return None


def _subscription_id(stripe_object: dict[str, Any]) -> str | None:
    if stripe_object.get("object") == "subscription":
        return _stripe_id(stripe_object)

    direct_subscription_id = _stripe_id(stripe_object.get("subscription"))
    if direct_subscription_id:
        return direct_subscription_id

    parent_subscription_id = _parent_subscription_id(stripe_object.get("parent"))
    if parent_subscription_id:
        return parent_subscription_id

    lines = stripe_object.get("lines")
    line_items = lines.get("data") if isinstance(lines, dict) else None
    if isinstance(line_items, list):
        for line_item in line_items:
            if not isinstance(line_item, dict):
                continue
            line_subscription_id = _stripe_id(line_item.get("subscription"))
            if line_subscription_id:
                return line_subscription_id
            line_parent_subscription_id = _parent_subscription_id(line_item.get("parent"))
            if line_parent_subscription_id:
                return line_parent_subscription_id

    return None


def _find_user_id_by_subscription(subscription_id: str | None) -> str | None:
    if not subscription_id:
        return None
    result = (
        get_supabase_client()
        .table("users")
        .select("id")
        .eq("stripe_subscription_id", subscription_id)
        .limit(1)
        .execute()
    )
    if result.data:
        return result.data[0]["id"]
    return None


def _find_user_id(stripe_object: dict[str, Any]) -> str | None:
    return _metadata_user_id(stripe_object) or _find_user_id_by_subscription(
        _subscription_id(stripe_object)
    )


def _get_existing_log(event_id: str) -> dict[str, Any] | None:
    result = (
        get_supabase_client()
        .table("webhook_log")
        .select("id, processed")
        .eq("source", "stripe")
        .eq("stripe_event_id", event_id)
        .limit(1)
        .execute()
    )
    return result.data[0] if result.data else None


def _insert_log(payload: dict[str, Any]) -> str | None:
    result = (
        get_supabase_client()
        .table("webhook_log")
        .insert(
            {
                "source": "stripe",
                "stripe_event_id": payload["id"],
                "stripe_event_type": payload["type"],
                "payload": payload,
                "processed": False,
                "duplicate": False,
            }
        )
        .execute()
    )
    if result.data:
        return result.data[0].get("id")
    return None


def _mark_log_processed(log_id: str | None) -> None:
    if not log_id:
        return
    get_supabase_client().table("webhook_log").update(
        {"processed": True, "processed_at": datetime.now(tz=timezone.utc).isoformat()}
    ).eq("id", log_id).execute()


def _insert_outbox(user_id: str, event_id: str, event_type: str, payload: dict[str, Any]) -> None:
    existing = (
        get_supabase_client()
        .table("billing_outbox")
        .select("id")
        .eq("stripe_event_id", event_id)
        .limit(1)
        .execute()
    )
    if existing.data:
        return

    get_supabase_client().table("billing_outbox").insert(
        {
            "user_id": user_id,
            "stripe_event_id": event_id,
            "event_type": event_type,
            "payload": payload,
        }
    ).execute()


def _insert_payment_history(
    user_id: str,
    event_id: str,
    stripe_object: dict[str, Any],
    payment_type: str,
) -> None:
    existing = (
        get_supabase_client()
        .table("payment_history")
        .select("id")
        .eq("stripe_event_id", event_id)
        .limit(1)
        .execute()
    )
    if existing.data:
        return

    amount = _coerce_money_pln(
        stripe_object.get("amount_total") or stripe_object.get("amount_paid")
    )
    get_supabase_client().table("payment_history").insert(
        {
            "user_id": user_id,
            "amount_pln": amount,
            "type": payment_type,
            "status": "paid",
            "stripe_event_id": event_id,
            "stripe_checkout_session_id": _stripe_id(stripe_object)
            if stripe_object.get("object") == "checkout.session"
            else None,
            "stripe_invoice_id": _stripe_id(stripe_object)
            if stripe_object.get("object") == "invoice"
            else None,
            "stripe_subscription_id": _subscription_id(stripe_object),
            "stripe_customer_id": _stripe_id(stripe_object.get("customer")),
            "currency": stripe_object.get("currency"),
        }
    ).execute()


def _handle_checkout_paid(payload: dict[str, Any], stripe_object: dict[str, Any]) -> dict[str, Any]:
    if stripe_object.get("payment_status") != "paid":
        return {"processed": True, "activated": False, "reason": "payment_not_paid"}

    user_id = _metadata_user_id(stripe_object)
    if not user_id:
        raise HTTPException(status_code=422, detail="Stripe session has no user_id metadata.")

    plan = _metadata_plan(stripe_object)
    update_data = {
        "subscription_status": "active",
        "subscription_plan": plan,
        "activation_paid": True,
        "stripe_customer_id": _stripe_id(stripe_object.get("customer")),
        "stripe_subscription_id": _stripe_id(stripe_object.get("subscription")),
        "stripe_checkout_session_id": _stripe_id(stripe_object),
        "updated_at": datetime.now(tz=timezone.utc).isoformat(),
    }
    get_supabase_client().table("users").update(update_data).eq("id", user_id).execute()
    _insert_payment_history(user_id, payload["id"], stripe_object, "stripe_checkout")
    _insert_outbox(user_id, payload["id"], "billing_activated", payload)
    return {"processed": True, "activated": True, "user_id": user_id}


def _handle_invoice(payload: dict[str, Any], stripe_object: dict[str, Any], paid: bool) -> dict[str, Any]:
    user_id = _find_user_id(stripe_object)
    if not user_id:
        raise HTTPException(status_code=422, detail="Invoice user could not be resolved.")

    update_data = {
        "subscription_status": "active" if paid else "past_due",
        "stripe_customer_id": _stripe_id(stripe_object.get("customer")),
        "stripe_subscription_id": _subscription_id(stripe_object),
        "subscription_current_period_end": _iso_from_stripe_timestamp(
            stripe_object.get("period_end")
        ),
        "updated_at": datetime.now(tz=timezone.utc).isoformat(),
    }
    get_supabase_client().table("users").update(update_data).eq("id", user_id).execute()

    if paid:
        _insert_payment_history(user_id, payload["id"], stripe_object, "stripe_invoice")

    _insert_outbox(
        user_id,
        payload["id"],
        "billing_invoice_paid" if paid else "billing_payment_failed",
        payload,
    )
    return {"processed": True, "user_id": user_id, "status": update_data["subscription_status"]}


def _handle_subscription(
    payload: dict[str, Any],
    stripe_object: dict[str, Any],
    deleted: bool = False,
) -> dict[str, Any]:
    user_id = _find_user_id(stripe_object)
    if not user_id:
        raise HTTPException(status_code=422, detail="Subscription user could not be resolved.")

    status_value = _subscription_status(stripe_object.get("status"), deleted=deleted)
    update_data = {
        "subscription_status": status_value,
        "subscription_plan": _metadata_plan(stripe_object),
        "stripe_customer_id": _stripe_id(stripe_object.get("customer")),
        "stripe_subscription_id": _stripe_id(stripe_object),
        "subscription_current_period_end": _iso_from_stripe_timestamp(
            stripe_object.get("current_period_end")
        ),
        "updated_at": datetime.now(tz=timezone.utc).isoformat(),
    }
    get_supabase_client().table("users").update(update_data).eq("id", user_id).execute()
    _insert_outbox(user_id, payload["id"], "billing_subscription_changed", payload)
    return {"processed": True, "user_id": user_id, "status": status_value}


def process_stripe_event(payload: dict[str, Any]) -> dict[str, Any]:
    event_type = payload.get("type")
    stripe_object = payload.get("object")
    if not isinstance(payload.get("id"), str) or not isinstance(event_type, str):
        raise HTTPException(status_code=400, detail="Invalid Stripe event payload.")
    if not isinstance(stripe_object, dict):
        raise HTTPException(status_code=400, detail="Stripe event object is missing.")
    if payload.get("livemode") is True:
        raise HTTPException(status_code=400, detail="Live Stripe events are disabled in Phase 0C.")

    existing_log = _get_existing_log(payload["id"])
    if existing_log and existing_log.get("processed"):
        return {"processed": False, "duplicate": True}

    log_id = existing_log.get("id") if existing_log else _insert_log(payload)

    if event_type in {"checkout.session.completed", "checkout.session.async_payment_succeeded"}:
        result = _handle_checkout_paid(payload, stripe_object)
    elif event_type == "invoice.payment_succeeded":
        result = _handle_invoice(payload, stripe_object, paid=True)
    elif event_type == "invoice.payment_failed":
        result = _handle_invoice(payload, stripe_object, paid=False)
    elif event_type == "customer.subscription.updated":
        result = _handle_subscription(payload, stripe_object)
    elif event_type == "customer.subscription.deleted":
        result = _handle_subscription(payload, stripe_object, deleted=True)
    else:
        result = {"processed": False, "ignored": True}

    _mark_log_processed(log_id)
    return result


@router.post("/stripe-event")
async def receive_stripe_event(
    request: Request,
    x_oze_timestamp: Annotated[str | None, Header()] = None,
    x_oze_signature: Annotated[str | None, Header()] = None,
):
    raw_body = await request.body()
    verify_internal_signature(raw_body, x_oze_timestamp, x_oze_signature)

    try:
        payload = json.loads(raw_body.decode("utf-8"))
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=400, detail="Invalid JSON payload.") from exc

    try:
        return process_stripe_event(payload)
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Stripe billing event failed")
        raise HTTPException(status_code=500, detail="Billing event failed.") from exc
