"""Single source of truth for Calendar action type presentation."""

from dataclasses import dataclass


@dataclass(frozen=True)
class ActionTypePresentation:
    label: str
    confirmation_heading: str
    success_message: str
    schedule_suffix: str
    description_prefix: str = ""


_PRESENTATION: dict[str, ActionTypePresentation] = {
    "in_person": ActionTypePresentation(
        label="Spotkanie",
        confirmation_heading="✅ Dodać spotkanie?",
        success_message="✅ Spotkanie dodane do kalendarza.",
        schedule_suffix="spotkanie",
    ),
    "phone_call": ActionTypePresentation(
        label="Telefon",
        confirmation_heading="✅ Dodać telefon?",
        success_message="✅ Telefon dodany do kalendarza.",
        schedule_suffix="telefon",
        description_prefix="📞 Zadzwoń do klienta.",
    ),
    "offer_email": ActionTypePresentation(
        label="Wysłać ofertę",
        confirmation_heading="✅ Dodać mail?",
        success_message="✅ Mail dodany do kalendarza.",
        schedule_suffix="mail",
        description_prefix="📧 Wyślij ofertę klientowi.",
    ),
    # Legacy Calendar metadata can still contain doc_followup. New routing maps
    # document reminders to phone_call, but rendering old events must stay sane.
    "doc_followup": ActionTypePresentation(
        label="Follow-up dokumentowy",
        confirmation_heading="✅ Dodać follow-up?",
        success_message="✅ Follow-up dodany do kalendarza.",
        schedule_suffix="follow-up",
        description_prefix="📋 Follow-up dokumentowy.",
    ),
}


def presentation_for(event_type: str | None) -> ActionTypePresentation:
    return _PRESENTATION.get(event_type or "", _PRESENTATION["in_person"])


def action_label(event_type: str | None) -> str:
    return presentation_for(event_type).label


def confirmation_heading(event_type: str | None) -> str:
    return presentation_for(event_type).confirmation_heading


def success_message(event_type: str | None) -> str:
    return presentation_for(event_type).success_message


def schedule_entry_suffix(event_type: str | None) -> str:
    return presentation_for(event_type).schedule_suffix


def description_prefix(event_type: str | None) -> str:
    return presentation_for(event_type).description_prefix


def calendar_title(event_type: str | None, client_name: str | None = "") -> str:
    label = action_label(event_type)
    name = (client_name or "").strip()
    return f"{label} — {name}" if name else label

