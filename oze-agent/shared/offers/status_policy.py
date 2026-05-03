"""Pipeline status policy for offer sends."""

OFFER_SENT_STATUS = "Oferta wysłana"
CAN_MOVE_TO_OFFER_SENT = {
    "",
    "Nowy lead",
    "Spotkanie umówione",
    "Spotkanie odbyte",
}
DO_NOT_MOVE_TO_OFFER_SENT = {
    OFFER_SENT_STATUS,
    "Podpisane",
    "Zamontowana",
    "Rezygnacja z umowy",
    "Nieaktywny",
    "Odrzucone",
}


def should_mark_offer_sent(current_status: str | None) -> bool:
    normalized = (current_status or "").strip()
    if normalized in DO_NOT_MOVE_TO_OFFER_SENT:
        return False
    return normalized in CAN_MOVE_TO_OFFER_SENT
