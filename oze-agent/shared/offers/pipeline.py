"""Confirmed offer-send pipeline."""

import inspect
from dataclasses import dataclass, field

from shared.google_sheets import update_client, update_client_fields_without_touch

from .email_utils import merge_offer_recipients
from .gmail import send_offer_email
from .pdf import render_offer_pdf
from .repository import OfferRepository
from .status_policy import OFFER_SENT_STATUS, should_mark_offer_sent


@dataclass(frozen=True)
class SendOfferResult:
    sent: bool
    already_sent: bool = False
    gmail_message_id: str | None = None
    recipients: list[str] = field(default_factory=list)
    invalid_recipients: list[str] = field(default_factory=list)
    sheets_errors: list[str] = field(default_factory=list)
    error: str | None = None


async def _maybe_await(value):
    if inspect.isawaitable(value):
        return await value
    return value


def _combined_email_field(current_value: str, new_emails: list[str]) -> str:
    existing = [part.strip() for part in (current_value or "").split(";") if part.strip()]
    lower = {item.lower() for item in existing}
    for email in new_emails:
        if email.lower() not in lower:
            existing.append(email)
            lower.add(email.lower())
    return "; ".join(existing)


async def send_offer_after_confirmation(
    *,
    user_id: str,
    telegram_id: int,
    idempotency_key: str,
    offer_number: int,
    template: dict,
    seller_profile: dict,
    client: dict,
    command_text: str,
    repository: OfferRepository | None = None,
    gmail_sender=None,
    update_email=None,
    update_status=None,
) -> SendOfferResult:
    """Send the PDF via Gmail, then best-effort update Sheets.

    Gmail/PDF is the primary effect. Sheets writes happen only after Gmail
    success and are reported as partial failures.
    """
    repo = repository or OfferRepository()
    merge = merge_offer_recipients(client.get("Email", ""), command_text)

    attempt = repo.ensure_send_attempt(
        idempotency_key=idempotency_key,
        user_id=user_id,
        telegram_id=telegram_id,
        client_row=client.get("_row"),
        client_name=client.get("Imię i nazwisko", ""),
        client_city=client.get("Miasto", ""),
        recipients=merge.recipients,
        invalid_recipients=merge.invalid_recipients,
        offer_template_id=template.get("id"),
        offer_template_name=template.get("name"),
        offer_number=offer_number,
    )
    if attempt.get("status") == "sent":
        return SendOfferResult(
            sent=True,
            already_sent=True,
            gmail_message_id=attempt.get("gmail_message_id"),
            recipients=[],
            invalid_recipients=[],
            sheets_errors=[],
        )

    claimed = repo.claim_send_attempt(idempotency_key)
    if not claimed:
        current = repo.get_send_attempt(idempotency_key) or {}
        if current.get("status") == "sent":
            return SendOfferResult(
                sent=True,
                already_sent=True,
                gmail_message_id=current.get("gmail_message_id"),
            )
        return SendOfferResult(
            sent=False,
            already_sent=True,
            error=current.get("error") or "send_already_in_progress",
        )

    if not merge.recipients:
        repo.mark_send_failed(idempotency_key, "missing_valid_email")
        return SendOfferResult(
            sent=False,
            recipients=[],
            invalid_recipients=merge.invalid_recipients,
            error="missing_valid_email",
        )

    try:
        pdf_bytes = render_offer_pdf(template, seller_profile, client)
        sender = gmail_sender or send_offer_email
        gmail_message_id = await _maybe_await(
            sender(user_id, merge.recipients, template, seller_profile, client, pdf_bytes)
        )
    except Exception as exc:
        repo.mark_send_failed(idempotency_key, str(exc))
        return SendOfferResult(
            sent=False,
            recipients=merge.recipients,
            invalid_recipients=merge.invalid_recipients,
            error=str(exc),
        )

    repo.mark_send_sent(idempotency_key, gmail_message_id or "")

    sheets_errors: list[str] = []
    row = client.get("_row")
    if row is not None and merge.new_emails_for_sheets:
        new_email_field = _combined_email_field(client.get("Email", ""), merge.new_emails_for_sheets)
        updater = update_email or (
            lambda uid, row_number, value: update_client_fields_without_touch(uid, row_number, {"Email": value})
        )
        ok = await _maybe_await(updater(user_id, row, new_email_field))
        if not ok:
            sheets_errors.append("email")

    if row is not None and should_mark_offer_sent(client.get("Status", "")):
        updater = update_status or (
            lambda uid, row_number, value: update_client(uid, row_number, {"Status": value})
        )
        ok = await _maybe_await(updater(user_id, row, OFFER_SENT_STATUS))
        if not ok:
            sheets_errors.append("status")

    return SendOfferResult(
        sent=True,
        gmail_message_id=gmail_message_id,
        recipients=merge.recipients,
        invalid_recipients=merge.invalid_recipients,
        sheets_errors=sheets_errors,
    )
