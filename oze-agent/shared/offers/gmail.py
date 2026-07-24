"""Gmail MIME construction and sending for offer PDFs."""

import base64
import hashlib
from email.message import EmailMessage

from googleapiclient.discovery import build

from shared.google_auth import get_google_credentials

from .email_template import DEFAULT_EMAIL_BODY_TEMPLATE, render_email_template
from .email_utils import sanitize_filename_part


def deterministic_message_id(idempotency_key: str) -> str:
    digest = hashlib.sha256(idempotency_key.encode("utf-8")).hexdigest()[:32]
    return f"<oze-offer-{digest}@agent-oze.local>"


def build_offer_email_body(template: dict, seller_profile: dict | None, client: dict) -> str:
    profile = seller_profile or {}
    return render_email_template(
        profile.get("email_body_template") or DEFAULT_EMAIL_BODY_TEMPLATE,
        client=client,
        template=template,
        seller_profile=profile,
    ).body


def build_offer_subject(template: dict, seller_profile: dict | None, client: dict) -> str:
    company = (seller_profile or {}).get("company_name") or "firma"
    client_name = client.get("Imię i nazwisko") or client.get("name") or "klient"
    return f"Oferta — {template.get('name', 'oferta')} — {company} — {client_name}"


def build_attachment_filename(client: dict, template: dict) -> str:
    client_name = sanitize_filename_part(client.get("Imię i nazwisko") or client.get("name") or "klient")
    template_name = sanitize_filename_part(template.get("name") or "oferta")
    return f"Oferta-{client_name}-{template_name}.pdf"


def build_offer_email_message(
    recipients: list[str],
    template: dict,
    seller_profile: dict | None,
    client: dict,
    pdf_bytes: bytes,
    message_id: str | None = None,
) -> EmailMessage:
    message = EmailMessage()
    message["To"] = ", ".join(recipients)
    if (seller_profile or {}).get("email"):
        message["From"] = (seller_profile or {})["email"]
    message["Subject"] = build_offer_subject(template, seller_profile, client)
    if message_id:
        message["Message-ID"] = message_id
    message.set_content(build_offer_email_body(template, seller_profile, client))
    message.add_attachment(
        pdf_bytes,
        maintype="application",
        subtype="pdf",
        filename=build_attachment_filename(client, template),
    )
    return message


def encode_gmail_raw_message(message: EmailMessage) -> str:
    return base64.urlsafe_b64encode(message.as_bytes()).decode("ascii")


def send_offer_email(
    user_id: str,
    recipients: list[str],
    template: dict,
    seller_profile: dict | None,
    client: dict,
    pdf_bytes: bytes,
    *,
    idempotency_key: str | None = None,
) -> str:
    creds = get_google_credentials(user_id)
    if not creds:
        raise RuntimeError("google_not_connected")
    service = build("gmail", "v1", credentials=creds, cache_discovery=False)
    message_id = deterministic_message_id(idempotency_key) if idempotency_key else None
    if message_id:
        existing = service.users().messages().list(
            userId="me",
            q=f"rfc822msgid:{message_id}",
            maxResults=1,
        ).execute()
        messages = existing.get("messages") or []
        if messages:
            return messages[0].get("id") or ""
    message = build_offer_email_message(
        recipients,
        template,
        seller_profile,
        client,
        pdf_bytes,
        message_id=message_id,
    )
    result = service.users().messages().send(
        userId="me",
        body={"raw": encode_gmail_raw_message(message)},
    ).execute()
    return result.get("id") or ""
