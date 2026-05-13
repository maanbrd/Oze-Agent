"""Deterministic meeting-location resolver for existing clients."""

from dataclasses import dataclass
import re


@dataclass(frozen=True)
class MeetingLocationResolution:
    location: str
    needs_address: bool = False


def _clean(value: object) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip(" ,.;")


def _looks_like_street_address(location: str) -> bool:
    text = _clean(location)
    if not text:
        return False
    return bool(re.search(r"\d", text)) or bool(re.match(r"(?i)^ul\.?\s+|^ulica\s+", text))


def _stored_location(existing_client: dict | None) -> str:
    client = existing_client or {}
    address = _clean(client.get("Adres"))
    if not address:
        return ""
    city = _clean(client.get("Miasto") or client.get("Miejscowość"))
    return ", ".join(part for part in (address, city) if part)


def _stored_city(existing_client: dict | None) -> str:
    client = existing_client or {}
    return _clean(client.get("Miasto") or client.get("Miejscowość"))


def resolve_meeting_location(
    *,
    event_type: str | None,
    command_location: str | None,
    existing_client: dict | None,
) -> MeetingLocationResolution:
    if event_type == "phone_call":
        return MeetingLocationResolution("telefonicznie")

    location = _clean(command_location)
    if _looks_like_street_address(location):
        return MeetingLocationResolution(location)

    stored = _stored_location(existing_client)
    if stored:
        stored_city = _stored_city(existing_client)
        if location and stored_city and location.casefold() != stored_city.casefold():
            return MeetingLocationResolution("", needs_address=True)
        return MeetingLocationResolution(stored)

    if location:
        return MeetingLocationResolution("", needs_address=True)

    return MeetingLocationResolution("")
