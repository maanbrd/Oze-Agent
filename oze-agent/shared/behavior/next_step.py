"""Deterministic next-step/R7 reply classifier."""

from dataclasses import dataclass
from enum import Enum
import re

from .client_field_update import ClientFieldUpdate, parse_client_field_update


class NextStepDecisionKind(Enum):
    CLOSE = "close"
    ACTION = "action"
    FIELD_UPDATE = "field_update"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class NextStepDecision:
    kind: NextStepDecisionKind
    event_type: str | None = None
    field_update: ClientFieldUpdate | None = None


_CLOSE_EXACT = {
    "/cancel",
    "anuluj",
    "nic",
    "nie",
    "nie.",
    "nie wiem",
    "nie wiem jeszcze",
    "no",
    "stop",
}
_CLOSE_MARKERS = ("później", "pozniej", "odłóż", "odloz", "odłożyć", "odlozyc")


def classify_next_step_reply(message_text: str) -> NextStepDecision:
    text = (message_text or "").strip()
    lower = text.casefold()
    if not text:
        return NextStepDecision(NextStepDecisionKind.UNKNOWN)

    field_update = parse_client_field_update(text)
    if field_update:
        return NextStepDecision(
            kind=NextStepDecisionKind.FIELD_UPDATE,
            field_update=field_update,
        )

    if lower in _CLOSE_EXACT or any(marker in lower for marker in _CLOSE_MARKERS):
        return NextStepDecision(NextStepDecisionKind.CLOSE)

    if re.search(r"\bspotkanie\b|\bum[oó]w\b|\bwizyta\b", lower):
        return NextStepDecision(NextStepDecisionKind.ACTION, event_type="in_person")

    if re.search(r"\btelefon\b|zadzwo|zadzwon|dzwoni|rozmowa telefoniczna", lower):
        return NextStepDecision(NextStepDecisionKind.ACTION, event_type="phone_call")

    if re.search(r"\bmail\b|\be-mail\b|\bemail\b|wyślij|wyslij|ofert", lower):
        return NextStepDecision(NextStepDecisionKind.ACTION, event_type="offer_email")

    return NextStepDecision(NextStepDecisionKind.UNKNOWN)

