"""Internal billing event ingestion routes."""

from __future__ import annotations

import hashlib
import hmac
import json
import os
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, HTTPException, Request, status

from bot.config import Config
from shared.database import get_supabase_client

router = APIRouter()

MAX_SIGNATURE_AGE_SECONDS = 300
SUPPORTED_EVENTS = {
    "checkout.session.completed",
    "checkout.session.async_payment_succeeded",
    "invoice.payment_succeeded",
    "invoice.payment_failed",
    "customer.subscription.updated",
    "customer.subscription.deleted",
}


def _now_iso() -> str:
    return datetime.now(tz=timezone.utc).isoformat()


def _env_value(name: str) -> str | None:
    value = (os.getenv(name) or "").strip()
    return value if value and value not in {'""', "''"} else None


def _billing_secret() -> str:
    secret = (getattr(Config, "BILLING_INTERNAL_SECRET", "") or "").strip() or _env_value("BILLING_INTERNAL_SECRET")
    if not secret:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Billing internal secret is not configured.",
        )
    return secret


def _expected_signature(body: bytes, timestamp: str, secret: str) -> str:
    digest = hmac.new(
        secret.encode(),
        f"{timestamp}.".encode() + body,
        hashlib.sha256,
    ).hexdigest()
    return f"sha256={digest}"


def verify_internal_signature(
    body: bytes,
    timestamp: str | None,
    signature: str,
    *,
    now: int | None = None,
) -> None:
    if not timestamp or not signature.startswith("sha256="):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing billing signature.",
        )

    try:
        timestamp_int = int(timestamp)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid billing timestamp.",
        ) from exc

    now_int = now if now is not None else int(datetime.now(tz=timezone.utc).timestamp())
    if abs(now_int - timestamp_int) > MAX_SIGNATURE_AGE_SECONDS:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Expired billing signature.",
        )

    expected = _expected_signature(body, timestamp, _billing_secret())
    if not hmac.compare_digest(expected, signature):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid billing signature.",
        )


def _verify_internal_signature(body: bytes, headers: dict[str, str]) -> None:
    verify_internal_signature(
        body,
        headers.get("x-oze-timestamp"),
        headers.get("x-oze-signature", ""),
    )


def _event_object(event: dict[str, Any]) -> dict[str, Any]:
    event_object = event.get("object")
    if not isinstance(event_object, dict):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Stripe event object is missing.",
        )
    return event_object


def _subscription_details(value: dict[str, Any]) -> dict[str, Any]:
    details = value.get("subscription_details")
    return details if isinstance(details, dict) else {}


def _stripe_livemode(event: dict[str, Any], event_object: dict[str, Any]) -> bool:
    details = _subscription_details(event_object)
    for value in (
        event_object.get("livemode"),
        details.get("livemode"),
        event.get("livemode"),
    ):
        if isinstance(value, bool):
            return value
    return False


def _stripe_timestamp_to_iso(value: Any) -> str | None:
    if value is None or value == "":
        return None
    if isinstance(value, (int, float)):
        return datetime.fromtimestamp(int(value), tz=timezone.utc).isoformat()
    text = str(value).strip()
    if not text:
        return None
    if text.isdigit():
        return datetime.fromtimestamp(int(text), tz=timezone.utc).isoformat()
    return text


def _first_subscription_item(value: dict[str, Any]) -> dict[str, Any]:
    items = value.get("items")
    if not isinstance(items, dict):
        return {}
    data = items.get("data")
    if not isinstance(data, list) or not data:
        return {}
    first = data[0]
    return first if isinstance(first, dict) else {}


def _invoice_lines(value: dict[str, Any]) -> list[dict[str, Any]]:
    lines = value.get("lines")
    if not isinstance(lines, dict):
        return []
    data = lines.get("data")
    if not isinstance(data, list):
        return []
    return [line for line in data if isinstance(line, dict)]


def _line_period_end(value: dict[str, Any]) -> Any:
    for line in _invoice_lines(value):
        period = line.get("period")
        if isinstance(period, dict) and period.get("end"):
            return period.get("end")
    return None


def _subscription_period_end(value: dict[str, Any]) -> str | None:
    details = _subscription_details(value)
    first_item = _first_subscription_item(value)
    return _stripe_timestamp_to_iso(
        details.get("current_period_end")
        or details.get("trial_end")
        or value.get("current_period_end")
        or value.get("trial_end")
        or first_item.get("current_period_end")
        or first_item.get("trial_end")
        or value.get("subscription_current_period_end")
        or _line_period_end(value)
    )


def _subscription_cancel_at_period_end(value: dict[str, Any]) -> bool:
    details = _subscription_details(value)
    for candidate in (
        value.get("cancel_at_period_end"),
        details.get("cancel_at_period_end"),
    ):
        if isinstance(candidate, bool):
            return candidate
    return False


def _metadata(value: dict[str, Any]) -> dict[str, Any]:
    metadata = value.get("metadata")
    return metadata if isinstance(metadata, dict) else {}


def _get_existing_log(event_id: str) -> dict[str, Any] | None:
    result = (
        get_supabase_client()
        .table("webhook_log")
        .select("*")
        .eq("stripe_event_id", event_id)
        .limit(1)
        .execute()
    )
    return result.data[0] if result.data else None


def _insert_log(payload: dict[str, Any]) -> str | None:
    event_id = str(payload.get("id") or "")
    result = (
        get_supabase_client()
        .table("webhook_log")
        .insert(
            {
                "source": "stripe",
                "stripe_event_id": event_id or None,
                "payload": payload,
                "processed": False,
                "duplicate": False,
            }
        )
        .execute()
    )
    if not result.data:
        return None
    return result.data[0].get("id") or result.data[0]


def _get_or_create_log(event: dict[str, Any], existing: dict[str, Any] | None) -> str | dict | None:
    if existing:
        return existing.get("id") or existing
    try:
        return _insert_log(event)
    except Exception:
        # A concurrent delivery may have won the unique stripe_event_id race.
        raced = _get_existing_log(str(event.get("id") or ""))
        if raced:
            return raced.get("id") or raced
        raise


def _event_target_user(event_type: str, obj: dict[str, Any]) -> dict[str, Any] | None:
    if event_type.startswith("checkout.session"):
        metadata = _metadata(obj)
        user_id = metadata.get("user_id") or obj.get("client_reference_id")
        return _find_user_by_id(str(user_id)) if user_id else None
    subscription_id = (
        obj.get("id") if event_type.startswith("customer.subscription")
        else _invoice_subscription_id(obj)
    )
    return _find_user_by_subscription_id(str(subscription_id)) if subscription_id else None


def _mark_log_processed(log_id: str | None) -> None:
    if not log_id:
        return
    if isinstance(log_id, dict):
        log_id["processed"] = True
        return
    get_supabase_client().table("webhook_log").update(
        {"processed": True}
    ).eq("id", log_id).execute()


def _insert_payment_history(
    user_id: str,
    event_id: str,
    obj: dict[str, Any],
    payment_type: str,
) -> None:
    amount = obj.get("amount_total", obj.get("amount_paid"))
    amount_pln = round(float(amount or 0) / 100, 2)
    get_supabase_client().table("payment_history").insert(
        {
            "user_id": user_id,
            "stripe_event_id": event_id,
            "stripe_checkout_session_id": obj.get("id") if obj.get("object") == "checkout.session" else None,
            "stripe_invoice_id": obj.get("id") if obj.get("object") == "invoice" else None,
            "stripe_subscription_id": _subscription_id_from_object(obj),
            "amount_pln": amount_pln,
            "currency": obj.get("currency"),
            "type": payment_type,
        }
    ).execute()


def _insert_outbox(
    user_id: str,
    event_id: str,
    event_type: str,
    payload: dict[str, Any],
) -> None:
    get_supabase_client().table("billing_outbox").insert(
        {
            "user_id": user_id,
            "stripe_event_id": event_id,
            "event_type": event_type,
            "payload": payload,
        }
    ).execute()


def _subscription_id_from_object(obj: dict[str, Any]) -> str | None:
    subscription_id = obj.get("subscription")
    if subscription_id:
        return str(subscription_id)
    parent = obj.get("parent")
    if isinstance(parent, dict):
        details = parent.get("subscription_details")
        if isinstance(details, dict) and details.get("subscription"):
            return str(details["subscription"])
    return None


def _metadata_from_object(obj: dict[str, Any]) -> dict[str, Any]:
    metadata = _metadata(obj)
    if metadata:
        return metadata
    parent = obj.get("parent")
    if isinstance(parent, dict):
        details = parent.get("subscription_details")
        if isinstance(details, dict):
            return _metadata(details)
    return {}


def _find_user_by_id(user_id: str) -> dict[str, Any]:
    result = (
        get_supabase_client()
        .table("users")
        .select("*")
        .eq("id", user_id)
        .limit(1)
        .execute()
    )
    if not result.data:
        raise HTTPException(status_code=404, detail="User not found.")
    return result.data[0]


def _update_user(user_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    update_payload = {
        key: value for key, value in payload.items() if value is not None
    }
    update_payload["updated_at"] = _now_iso()

    def run_update(data: dict[str, Any]):
        return (
            get_supabase_client()
            .table("users")
            .update(data)
            .eq("id", user_id)
            .execute()
        )

    try:
        result = run_update(update_payload)
    except Exception as exc:
        message = str(exc)
        missing_cancel_column = (
            "subscription_cancel_at_period_end" in update_payload
            and "subscription_cancel_at_period_end" in message
            and (
                "PGRST204" in message
                or "schema cache" in message
                or "column" in message
            )
        )
        if not missing_cancel_column:
            raise
        retry_payload = dict(update_payload)
        retry_payload.pop("subscription_cancel_at_period_end", None)
        result = run_update(retry_payload)
    return result.data[0] if result.data else update_payload


def _log_event(event: dict[str, Any], processed: bool) -> None:
    event_object = event.get("object")
    normalized_object = event_object if isinstance(event_object, dict) else {}
    try:
        get_supabase_client().table("webhook_log").insert(
            {
                "source": "stripe",
                "payload": event,
                "processed": processed,
                "duplicate": False,
                "stripe_event_id": event.get("id") or "",
                "stripe_event_type": event.get("type") or "",
                "stripe_livemode": _stripe_livemode(event, normalized_object),
                "processed_at": _now_iso() if processed else None,
            }
        ).execute()
    except Exception:
        # Billing state must not fail because observability storage is unavailable.
        return


def _find_user_by_subscription_id(subscription_id: str) -> dict[str, Any] | None:
    result = (
        get_supabase_client()
        .table("users")
        .select("*")
        .eq("stripe_subscription_id", subscription_id)
        .limit(1)
        .execute()
    )
    return result.data[0] if result.data else None


def _invoice_subscription_id(invoice: dict[str, Any]) -> str | None:
    subscription_id = invoice.get("subscription")
    if isinstance(subscription_id, str) and subscription_id:
        return subscription_id

    parent = invoice.get("parent")
    if isinstance(parent, dict):
        subscription_details = parent.get("subscription_details")
        if isinstance(subscription_details, dict):
            subscription_id = subscription_details.get("subscription")
            if isinstance(subscription_id, str) and subscription_id:
                return subscription_id

    for line in _invoice_lines(invoice):
        line_subscription_id = line.get("subscription")
        if isinstance(line_subscription_id, str) and line_subscription_id:
            return line_subscription_id

        parent = line.get("parent")
        if not isinstance(parent, dict):
            continue
        subscription_item_details = parent.get("subscription_item_details")
        if not isinstance(subscription_item_details, dict):
            continue
        subscription_id = subscription_item_details.get("subscription")
        if isinstance(subscription_id, str) and subscription_id:
            return subscription_id

    return None


def _stripe_amount_pln(value: dict[str, Any]) -> float:
    amount = (
        value.get("amount_total")
        or value.get("amount_paid")
        or value.get("amount_due")
        or 0
    )
    try:
        return round(float(amount) / 100, 2)
    except (TypeError, ValueError):
        return 0.0


def _event_subscription_id(event_object: dict[str, Any]) -> str:
    if event_object.get("object") == "invoice":
        return _invoice_subscription_id(event_object) or ""
    value = event_object.get("subscription") or event_object.get("id") or ""
    return str(value) if value else ""


def _payment_snapshot_exists(payload: dict[str, Any]) -> bool:
    checks = [
        ("stripe_event_id", payload.get("stripe_event_id")),
        ("stripe_checkout_session_id", payload.get("stripe_checkout_session_id")),
        ("stripe_invoice_id", payload.get("stripe_invoice_id")),
    ]
    for key, value in checks:
        if not value:
            continue
        try:
            result = (
                get_supabase_client()
                .table("payment_history")
                .select("id")
                .eq(key, value)
                .limit(1)
                .execute()
            )
        except Exception:
            continue
        if result.data:
            return True
    return False


def _log_payment_snapshot(
    *,
    event: dict[str, Any],
    event_object: dict[str, Any],
    user_id: str,
    status_value: str,
) -> None:
    payload = {
        "user_id": user_id,
        "amount_pln": _stripe_amount_pln(event_object),
        "type": event.get("type") or "",
        "status": status_value,
        "stripe_event_id": event.get("id") or "",
        "stripe_checkout_session_id": (
            event_object.get("id")
            if event_object.get("object") == "checkout.session"
            else ""
        ),
        "stripe_invoice_id": (
            event_object.get("id")
            if event_object.get("object") == "invoice"
            else ""
        ),
        "stripe_subscription_id": _event_subscription_id(event_object),
        "stripe_customer_id": event_object.get("customer") or "",
        "currency": event_object.get("currency") or "",
        "stripe_livemode": _stripe_livemode(event, event_object),
    }
    try:
        if _payment_snapshot_exists(payload):
            return
        get_supabase_client().table("payment_history").insert(payload).execute()
    except Exception:
        return


def process_stripe_event(event: dict[str, Any]) -> dict[str, Any]:
    event_id = str(event.get("id") or "").strip()
    if not event_id:
        raise HTTPException(status_code=400, detail="Stripe event id is missing.")

    existing = _get_existing_log(event_id)
    if existing and existing.get("processed"):
        return {"processed": False, "duplicate": True}

    log_id = _get_or_create_log(event, existing)
    event_type = event.get("type")
    if event_type not in SUPPORTED_EVENTS:
        _mark_log_processed(log_id)
        return {"processed": False, "duplicate": False}

    event_object = _event_object(event)
    event_created = int(event.get("created") or 0)
    target_user = _event_target_user(str(event_type), event_object)
    last_created = int((target_user or {}).get("last_stripe_event_created") or 0)
    if event_created and last_created > event_created:
        _mark_log_processed(log_id)
        return {
            "processed": False,
            "duplicate": False,
            "stale": True,
            "user_id": (target_user or {}).get("id"),
        }
    updated: dict[str, Any] | None = None

    if event_type in {
        "checkout.session.completed",
        "checkout.session.async_payment_succeeded",
    }:
        updated = _activate_from_checkout_session(event_object)
        if updated:
            if updated.get("activation_paid"):
                _log_payment_snapshot(
                    event=event,
                    event_object=event_object,
                    user_id=updated["id"],
                    status_value="paid",
                )
            _insert_outbox(updated["id"], event_id, "billing_activated", event)
    elif event_type == "invoice.payment_succeeded":
        subscription_id = _invoice_subscription_id(event_object)
        if subscription_id:
            details = _subscription_details(event_object)
            updated = _update_from_subscription(
                {
                    **details,
                    "id": subscription_id,
                    "status": details.get("status") or "active",
                    "livemode": details.get("livemode", event_object.get("livemode")),
                    "current_period_end": (
                        details.get("current_period_end")
                        or _line_period_end(event_object)
                        or event_object.get("period_end")
                    ),
                }
            )
            if updated:
                _log_payment_snapshot(
                    event=event,
                    event_object=event_object,
                    user_id=updated["id"],
                    status_value="paid",
                )
                _insert_outbox(updated["id"], event_id, "billing_invoice_paid", event)
    elif event_type == "invoice.payment_failed":
        updated = _mark_invoice_failed(event_object)
        if updated:
            _log_payment_snapshot(
                event=event,
                event_object=event_object,
                user_id=updated["id"],
                status_value="failed",
            )
    elif event_type == "customer.subscription.updated":
        updated = _update_from_subscription(event_object)
        if updated:
            _log_payment_snapshot(
                event=event,
                event_object=event_object,
                user_id=updated["id"],
                status_value=updated.get("subscription_status", "active"),
            )
    elif event_type == "customer.subscription.deleted":
        updated = _update_from_subscription(event_object, deleted=True)
        if updated:
            _log_payment_snapshot(
                event=event,
                event_object=event_object,
                user_id=updated["id"],
                status_value="canceled",
            )

    if updated:
        if event_created:
            updated = _update_user(
                updated["id"],
                {"last_stripe_event_created": event_created},
            )
        _mark_log_processed(log_id)
    return {
        "processed": updated is not None,
        "duplicate": False,
        "user_id": updated.get("id") if updated else None,
    }


def _activate_from_checkout_session(session: dict[str, Any]) -> dict[str, Any]:
    metadata = _metadata(session)
    user_id = metadata.get("user_id") or session.get("client_reference_id")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Checkout session has no user reference.",
        )

    if (
        session.get("object") != "checkout.session"
        or session.get("mode") != "subscription"
        or session.get("status") != "complete"
        or session.get("payment_status") not in {"paid", "no_payment_required"}
    ):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Checkout session is not paid.",
        )

    user = _find_user_by_id(str(user_id))
    metadata_auth_user_id = metadata.get("auth_user_id")
    if metadata_auth_user_id and metadata_auth_user_id != user.get("auth_user_id"):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Checkout session does not match the authenticated user.",
        )

    details = _subscription_details(session)
    is_trial = (
        session.get("payment_status") == "no_payment_required"
        or details.get("status") == "trialing"
    )

    updated = _update_user(
        user["id"],
        {
            "subscription_status": "trialing" if is_trial else "active",
            "subscription_plan": metadata.get("plan"),
            "activation_paid": not is_trial,
            "stripe_customer_id": session.get("customer"),
            "stripe_subscription_id": session.get("subscription"),
            "stripe_checkout_session_id": session.get("id"),
            "subscription_current_period_end": _subscription_period_end(session),
            "stripe_livemode": _stripe_livemode({}, session),
            "subscription_cancel_at_period_end": _subscription_cancel_at_period_end(session),
        },
    )
    return updated


def _update_from_subscription(
    subscription: dict[str, Any],
    *,
    deleted: bool = False,
) -> dict[str, Any] | None:
    subscription_id = subscription.get("id")
    if not subscription_id:
        return None

    result = (
        get_supabase_client()
        .table("users")
        .select("*")
        .eq("stripe_subscription_id", subscription_id)
        .limit(1)
        .execute()
    )
    if not result.data:
        return None

    status_value = "canceled" if deleted else subscription.get("status")
    if status_value == "canceled":
        subscription_status = "canceled"
        activation_paid = False
    elif status_value == "trialing":
        subscription_status = "trialing"
        activation_paid = False
    elif status_value in {"past_due", "unpaid", "incomplete", "incomplete_expired"}:
        subscription_status = "pending_payment"
        activation_paid = False
    else:
        subscription_status = "active"
        activation_paid = True

    return _update_user(
        result.data[0]["id"],
        {
            "subscription_status": subscription_status,
            "activation_paid": activation_paid,
            "stripe_subscription_id": subscription_id,
            "subscription_current_period_end": _subscription_period_end(subscription),
            "stripe_livemode": _stripe_livemode({}, subscription),
            "subscription_cancel_at_period_end": _subscription_cancel_at_period_end(subscription),
        },
    )


def _mark_invoice_failed(invoice: dict[str, Any]) -> dict[str, Any] | None:
    subscription_id = _invoice_subscription_id(invoice)
    if not subscription_id:
        return None
    user = _find_user_by_subscription_id(subscription_id)
    if not user:
        return None
    return _update_user(
        user["id"],
        {
            "subscription_status": "pending_payment",
            "activation_paid": False,
            "stripe_subscription_id": subscription_id,
            "subscription_current_period_end": _subscription_period_end(invoice),
            "stripe_livemode": _stripe_livemode({}, invoice),
            "subscription_cancel_at_period_end": _subscription_cancel_at_period_end(invoice),
        },
    )


async def process_signed_stripe_event(
    body: bytes,
    headers: dict[str, str],
) -> dict[str, Any]:
    _verify_internal_signature(body, {key.lower(): value for key, value in headers.items()})
    try:
        event = json.loads(body.decode("utf-8"))
    except json.JSONDecodeError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid Stripe event JSON.",
        ) from exc

    result = process_stripe_event(event)
    response = {
        "received": True,
        "processed": result.get("processed", False),
    }
    if result.get("duplicate"):
        response["duplicate"] = True
    return response


@router.post("/stripe-event")
async def stripe_event(request: Request):
    return await process_signed_stripe_event(
        await request.body(),
        {
            "x-oze-timestamp": request.headers.get("x-oze-timestamp", ""),
            "x-oze-signature": request.headers.get("x-oze-signature", ""),
        },
    )
