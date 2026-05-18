"""Google Calendar mirror helpers for the owner-facing admin calendar."""

from __future__ import annotations

from datetime import datetime


def _text(value) -> str:
    return "" if value is None else str(value)


def _user_name(user: dict) -> str:
    return _text(user.get("name") or user.get("email") or user.get("id"))


def _source_key(user: dict, event: dict) -> str:
    return ":".join([
        _text(user.get("id")),
        _text(user.get("google_calendar_id")),
        _text(event.get("id")),
    ])


def _time_body(value: str) -> dict:
    if "T" in value:
        return {"dateTime": value}
    return {"date": value}


def build_mirror_calendar_event(user: dict, event: dict) -> dict:
    """Return an idempotent admin-calendar event body for a source event."""
    key = _source_key(user, event)
    title = _text(event.get("title") or "Wydarzenie")
    description_parts = [
        "Kopia administracyjna Agent-OZE.",
        f"Użytkownik: {_user_name(user)} <{_text(user.get('email'))}>",
        f"Source user ID: {_text(user.get('id'))}",
        f"Source calendar ID: {_text(user.get('google_calendar_id'))}",
        f"Source event ID: {_text(event.get('id'))}",
    ]
    source_description = _text(event.get("description")).strip()
    if source_description:
        description_parts.extend(["", source_description])

    body = {
        "summary": f"[{_user_name(user)}] {title}",
        "description": "\n".join(description_parts),
        "start": _time_body(_text(event.get("start"))),
        "end": _time_body(_text(event.get("end"))),
        "extendedProperties": {
            "private": {
                "oze_admin_mirror": "true",
                "admin_mirror_key": key,
                "source_user_id": _text(user.get("id")),
                "source_calendar_id": _text(user.get("google_calendar_id")),
                "source_event_id": _text(event.get("id")),
                "source_event_type": _text(event.get("event_type")),
            }
        },
    }
    if event.get("location"):
        body["location"] = _text(event.get("location"))
    return {"key": key, "user_id": _text(user.get("id")), "body": body}


def _mirror_key(event: dict) -> str:
    private = event.get("extendedProperties", {}).get("private", {})
    if private.get("oze_admin_mirror") != "true":
        return ""
    return _text(private.get("admin_mirror_key"))


def _source_user_id(event: dict) -> str:
    private = event.get("extendedProperties", {}).get("private", {})
    return _text(private.get("source_user_id"))


def sync_admin_calendar_events(
    service,
    calendar_id: str,
    desired_events: list[dict],
    *,
    now: datetime,
    preserve_source_user_ids: set[str] | None = None,
) -> dict[str, int]:
    """Create/update/delete future admin mirror events idempotently."""
    preserve_source_user_ids = preserve_source_user_ids or set()
    existing_result = service.events().list(
        calendarId=calendar_id,
        timeMin=now.isoformat(),
        singleEvents=True,
        orderBy="startTime",
        maxResults=2500,
    ).execute()
    existing_by_key = {
        key: event
        for event in existing_result.get("items", [])
        if (key := _mirror_key(event))
    }

    created = updated = deleted = 0
    desired_keys = {item["key"] for item in desired_events}

    for item in desired_events:
        existing = existing_by_key.get(item["key"])
        if existing:
            service.events().update(
                calendarId=calendar_id,
                eventId=existing["id"],
                body=item["body"],
            ).execute()
            updated += 1
        else:
            service.events().insert(
                calendarId=calendar_id,
                body=item["body"],
            ).execute()
            created += 1

    for key, event in existing_by_key.items():
        if key in desired_keys:
            continue
        if _source_user_id(event) in preserve_source_user_ids:
            continue
        service.events().delete(calendarId=calendar_id, eventId=event["id"]).execute()
        deleted += 1

    return {"created": created, "updated": updated, "deleted": deleted}
