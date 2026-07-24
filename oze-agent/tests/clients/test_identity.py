from unittest.mock import AsyncMock, patch

import pytest


def _row(row: int, name: str, city: str, phone: str = "", email: str = "") -> dict:
    return {
        "_row": row,
        "Imię i nazwisko": name,
        "Miasto": city,
        "Telefon": phone,
        "Email": email,
    }


def test_build_client_ref_captures_identity_and_row_hint():
    from shared.clients.identity import build_client_ref

    ref = build_client_ref(
        _row(7, "Jan Żółć", "Łódź", "+48 600 100 200", "JAN@EXAMPLE.COM")
    )

    assert ref == {
        "version": 1,
        "row_hint": 7,
        "name": "jan zolc",
        "city": "lodz",
        "phone": "48600100200",
        "email": "jan@example.com",
    }


@pytest.mark.asyncio
async def test_resolve_client_ref_finds_same_client_after_row_move():
    from shared.clients.identity import build_client_ref, resolve_client_ref

    ref = build_client_ref(
        _row(7, "Jan Kowalski", "Warszawa", "600100200", "jan@example.com")
    )
    moved = _row(12, "Jan Kowalski", "Warszawa", "600100200", "jan@example.com")
    with patch(
        "shared.clients.identity.get_all_clients_or_raise",
        new=AsyncMock(return_value=[_row(7, "Adam Nowak", "Radom"), moved]),
    ):
        resolved = await resolve_client_ref("user-1", ref)

    assert resolved["_row"] == 12


@pytest.mark.asyncio
async def test_resolve_client_ref_rejects_ambiguous_name_city_without_anchor():
    from shared.clients.identity import ClientIdentityError, resolve_client_ref

    ref = {
        "version": 1,
        "row_hint": 7,
        "name": "jan kowalski",
        "city": "warszawa",
        "phone": "",
        "email": "",
    }
    rows = [
        _row(7, "Jan Kowalski", "Warszawa"),
        _row(12, "Jan Kowalski", "Warszawa"),
    ]
    with patch(
        "shared.clients.identity.get_all_clients_or_raise",
        new=AsyncMock(return_value=rows),
    ), pytest.raises(ClientIdentityError, match="client_identity_ambiguous"):
        await resolve_client_ref("user-1", ref)


@pytest.mark.asyncio
async def test_resolve_client_ref_rejects_reused_row():
    from shared.clients.identity import ClientIdentityError, resolve_client_ref

    ref = {
        "version": 1,
        "row_hint": 7,
        "name": "jan kowalski",
        "city": "warszawa",
        "phone": "600100200",
        "email": "jan@example.com",
    }
    with patch(
        "shared.clients.identity.get_all_clients_or_raise",
        new=AsyncMock(return_value=[_row(7, "Adam Nowak", "Radom")]),
    ), pytest.raises(ClientIdentityError, match="client_identity_not_found"):
        await resolve_client_ref("user-1", ref)
