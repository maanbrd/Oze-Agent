"""Internal billing event ingestion routes."""

from __future__ import annotations

import hashlib
import hmac
import json
import os
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, HTTPException, Request, status

from shared.database import get_supabase_client

router = APIRouter()

MAX_SIGNATURE_AGE_SECONDS = 300
SUPPORTED_EVENTS = {
    "checkout.session.completed",
    "checkout.session.async_payment_succeeded",
    "invoice.payment_succeeded",
    "customer.subscription.updated",
    "customer.subscription.deleted",
}


def _now_iso() -> str:
    return datetime.now(tz=timezone.utc).isoformat()


def _env_value(name: str) -> str | None:
    value = (os.getenv(name) or "").strip()
    return value if value and value not in {'""', "''"} else None


def _billing_secret() -> str:
    secret = _env_value("BILLING_INTERNAL_SECRET")
    if not secret:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Billing internal secret is not configured.",
        )
    return secret


def _verify_internal_signature(body: bytes, headers: dict[str, str]) -> None:
    timestamp = headers.get("x-oze-timestamp")
    signature = headers.get("x-oze-signature", "")
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

    now = int(datetime.now(tz=timezone.utc).timestamp())
    if abs(now - timestamp_int) > MAX_SIGNATURE_AGE_SECONDS:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Expired billing signature.",
        )

    expected = hmac.new(
        _billing_secret().encode(),
        f"{timestamp}.".encode() + body,
        hashlib.sha256,
    ).hexdigest()
    actual = signature.removeprefix("sha256=")
    if not hmac.compare_digest(expected, actual):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid billing signature.",
        )


def _event_object(event: dict[str, Any]) -> dict[str, Any]:
    event_object = event.get("object")
    if not isinstance(event_object, dict):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Stripe event object is missing.",
        )
    return event_object


def _metadata(value: dict[str, Any]) -> dict[str, Any]:
    metadata = value.get("metadata")
    return metadata if isinstance(metadata, dict) else {}


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
    result = (
        get_supabase_client()
        .table("users")
        .update(update_payload)
        .eq("id", user_id)
        .execute()
    )
    return result.data[0] if result.data else update_payload


def _log_event(event: dict[str, Any], processed: bool) -> None:
    try:
        get_supabase_client().table("webhook_log").insert(
            {
                "source": "stripe",
                "payload": event,
                "processed": processed,
                "duplicate": False,
            }
        ).execute()
    except Exception:
        # Billing state must not fail because observability storage is unavailable.
        return


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
        or session.get("payment_status") != "paid"
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

    return _update_user(
        user["id"],
        {
            "subscription_status": "active",
            "subscription_plan": metadata.get("plan"),
            "activation_paid": True,
            "stripe_customer_id": session.get("customer"),
            "stripe_subscription_id": session.get("subscription"),
            "stripe_checkout_session_id": session.get("id"),
            "subscription_current_period_end": session.get(
                "subscription_current_period_end"
            ),
        },
    )


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
    return _update_user(
        result.data[0]["id"],
        {
            "subscription_status": "canceled"
            if status_value == "canceled"
            else "active",
            "activation_paid": status_value != "canceled",
            "stripe_subscription_id": subscription_id,
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

    event_type = event.get("type")
    if event_type not in SUPPORTED_EVENTS:
        _log_event(event, processed=False)
        return {"received": True, "processed": False}

    event_object = _event_object(event)
    updated: dict[str, Any] | None = None
    if event_type in {
        "checkout.session.completed",
        "checkout.session.async_payment_succeeded",
    }:
        updated = _activate_from_checkout_session(event_object)
    elif event_type == "invoice.payment_succeeded":
        subscription_id = event_object.get("subscription")
        if subscription_id:
            updated = _update_from_subscription({"id": subscription_id, "status": "active"})
    elif event_type == "customer.subscription.updated":
        updated = _update_from_subscription(event_object)
    elif event_type == "customer.subscription.deleted":
        updated = _update_from_subscription(event_object, deleted=True)

    _log_event(event, processed=updated is not None)
    return {
        "received": True,
        "processed": updated is not None,
        "eventId": event.get("id"),
        "type": event_type,
    }


@router.post("/stripe-event")
async def stripe_event(request: Request):
    return await process_signed_stripe_event(
        await request.body(),
        {
            "x-oze-timestamp": request.headers.get("x-oze-timestamp", ""),
            "x-oze-signature": request.headers.get("x-oze-signature", ""),
        },
    )
