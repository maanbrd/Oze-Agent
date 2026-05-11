"""Supabase repository for offer templates, profiles and send attempts."""

from datetime import datetime, timedelta, timezone
from uuid import uuid4

from shared.database import get_supabase_client

READY_STATUS = "ready"
DRAFT_STATUS = "draft"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _expires_90_days() -> str:
    return (datetime.now(timezone.utc) + timedelta(days=90)).isoformat()


class OfferRepository:
    def __init__(self, client=None):
        self.client = client or get_supabase_client()

    def list_templates(self, user_id: str) -> list[dict]:
        result = (
            self.client.table("offer_templates")
            .select("*")
            .eq("user_id", user_id)
            .order("status")
            .order("sort_order")
            .order("created_at", desc=True)
            .execute()
        )
        return result.data or []

    def list_ready_templates(self, user_id: str) -> list[dict]:
        result = (
            self.client.table("offer_templates")
            .select("*")
            .eq("user_id", user_id)
            .eq("status", READY_STATUS)
            .order("sort_order")
            .execute()
        )
        return result.data or []

    def get_template(self, user_id: str, template_id: str) -> dict | None:
        result = (
            self.client.table("offer_templates")
            .select("*")
            .eq("user_id", user_id)
            .eq("id", template_id)
            .limit(1)
            .execute()
        )
        return result.data[0] if result.data else None

    def create_template(self, user_id: str, data: dict) -> dict | None:
        payload = _clean_template_payload(data)
        payload["user_id"] = user_id
        payload.setdefault("status", DRAFT_STATUS)
        payload.setdefault("sort_order", None)
        result = self.client.table("offer_templates").insert(payload).execute()
        return result.data[0] if result.data else None

    def update_template(self, user_id: str, template_id: str, data: dict) -> dict | None:
        payload = _clean_template_payload(data)
        payload["updated_at"] = _now_iso()
        result = (
            self.client.table("offer_templates")
            .update(payload)
            .eq("user_id", user_id)
            .eq("id", template_id)
            .execute()
        )
        return result.data[0] if result.data else None

    def delete_template(self, user_id: str, template_id: str) -> bool:
        self.client.table("offer_templates").delete().eq("user_id", user_id).eq("id", template_id).execute()
        self.reindex_ready(user_id)
        return True

    def duplicate_as_draft(self, user_id: str, template_id: str) -> dict | None:
        source = self.get_template(user_id, template_id)
        if not source:
            return None
        clone = {k: v for k, v in source.items() if k not in {"id", "created_at", "updated_at", "user_id"}}
        clone["name"] = f"{source.get('name', 'Oferta')} — kopia"
        clone["status"] = DRAFT_STATUS
        clone["sort_order"] = None
        return self.create_template(user_id, clone)

    def next_ready_sort_order(self, user_id: str) -> int:
        ready = self.list_ready_templates(user_id)
        values = [int(t.get("sort_order") or 0) for t in ready]
        return (max(values) if values else 0) + 10

    def publish_template(self, user_id: str, template_id: str) -> dict | None:
        return self.update_template(
            user_id,
            template_id,
            {"status": READY_STATUS, "sort_order": self.next_ready_sort_order(user_id)},
        )

    def reorder_ready(self, user_id: str, ordered_template_ids: list[str]) -> list[dict]:
        updated: list[dict] = []
        for idx, template_id in enumerate(ordered_template_ids, start=1):
            row = self.update_template(
                user_id,
                template_id,
                {"status": READY_STATUS, "sort_order": idx * 10},
            )
            if row:
                updated.append(row)
        return updated

    def reindex_ready(self, user_id: str) -> None:
        ready = self.list_ready_templates(user_id)
        self.reorder_ready(user_id, [row["id"] for row in ready])

    def get_seller_profile(self, user_id: str) -> dict:
        result = (
            self.client.table("offer_seller_profiles")
            .select("*")
            .eq("user_id", user_id)
            .limit(1)
            .execute()
        )
        profile = result.data[0] if result.data else {}
        logo_path = profile.get("logo_path")
        if logo_path:
            try:
                profile["logo_bytes"] = self.client.storage.from_("offer-logos").download(logo_path)
            except Exception:
                profile["logo_bytes"] = None
        return profile

    def upsert_seller_profile(self, user_id: str, data: dict) -> dict | None:
        payload = {
            key: value
            for key, value in data.items()
            if key in {
                "company_name",
                "logo_path",
                "accent_color",
                "email_signature",
                "email_body_template",
                "seller_name",
                "phone",
                "email",
            }
        }
        payload["user_id"] = user_id
        payload["updated_at"] = _now_iso()
        result = self.client.table("offer_seller_profiles").upsert(payload).execute()
        return result.data[0] if result.data else None

    def upload_logo(self, user_id: str, filename: str, content: bytes, content_type: str) -> str:
        ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else "png"
        path = f"{user_id}/{uuid4()}.{ext}"
        self.client.storage.from_("offer-logos").upload(
            path,
            content,
            {"content-type": content_type, "upsert": "true"},
        )
        return path

    def ensure_send_attempt(self, **kwargs) -> dict:
        payload = {
            **kwargs,
            "status": kwargs.get("status") or "pending",
            "expires_at": kwargs.get("expires_at") or _expires_90_days(),
        }
        try:
            result = self.client.table("offer_send_attempts").insert(payload).execute()
            if result.data:
                return result.data[0]
        except Exception:
            pass
        existing = self.get_send_attempt(kwargs["idempotency_key"])
        if existing:
            return existing
        raise RuntimeError("offer_attempt_create_failed")

    def claim_send_attempt(self, idempotency_key: str) -> dict | None:
        result = (
            self.client.table("offer_send_attempts")
            .update({"status": "sending", "updated_at": _now_iso()})
            .eq("idempotency_key", idempotency_key)
            .eq("status", "pending")
            .execute()
        )
        return result.data[0] if result.data else None

    def get_send_attempt(self, idempotency_key: str) -> dict | None:
        result = (
            self.client.table("offer_send_attempts")
            .select("*")
            .eq("idempotency_key", idempotency_key)
            .limit(1)
            .execute()
        )
        return result.data[0] if result.data else None

    def mark_send_sent(self, idempotency_key: str, gmail_message_id: str) -> None:
        self.client.table("offer_send_attempts").update({
            "status": "sent",
            "gmail_message_id": gmail_message_id,
            "sent_at": _now_iso(),
            "updated_at": _now_iso(),
            "error": None,
        }).eq("idempotency_key", idempotency_key).execute()

    def mark_send_failed(self, idempotency_key: str, error: str) -> None:
        self.client.table("offer_send_attempts").update({
            "status": "failed",
            "error": error[:1000],
            "updated_at": _now_iso(),
        }).eq("idempotency_key", idempotency_key).execute()


def _clean_template_payload(data: dict) -> dict:
    allowed = {
        "name",
        "status",
        "product_type",
        "price_net_pln",
        "vat_rate",
        "subsidy_amount_pln",
        "pv_power_kwp",
        "storage_capacity_kwh",
        "panel_brand",
        "panel_model",
        "inverter_brand",
        "inverter_model",
        "storage_brand",
        "storage_model",
        "construction",
        "protections_ac_dc",
        "installation",
        "monitoring_ems",
        "warranty",
        "payment_terms",
        "implementation_time",
        "validity",
        "sort_order",
    }
    return {key: value for key, value in data.items() if key in allowed}
