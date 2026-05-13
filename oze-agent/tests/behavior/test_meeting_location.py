from shared.behavior.meeting_location import resolve_meeting_location


def test_existing_client_physical_meeting_reuses_saved_address_when_command_has_only_city():
    result = resolve_meeting_location(
        event_type="in_person",
        command_location="Zielonka",
        existing_client={"Adres": "Czeska 20D", "Miasto": "Zielonka"},
    )

    assert result.location == "Czeska 20D, Zielonka"
    assert result.needs_address is False


def test_physical_meeting_without_street_address_requests_address():
    result = resolve_meeting_location(
        event_type="in_person",
        command_location="Zielonka",
        existing_client={"Miasto": "Zielonka"},
    )

    assert result.location == ""
    assert result.needs_address is True


def test_existing_client_city_only_location_different_from_saved_city_requests_address():
    result = resolve_meeting_location(
        event_type="in_person",
        command_location="Marki",
        existing_client={"Adres": "Czeska 20D", "Miasto": "Zielonka"},
    )

    assert result.location == ""
    assert result.needs_address is True


def test_phone_call_location_is_telefonicznie():
    result = resolve_meeting_location(
        event_type="phone_call",
        command_location="Zielonka",
        existing_client={"Adres": "Czeska 20D", "Miasto": "Zielonka"},
    )

    assert result.location == "telefonicznie"
    assert result.needs_address is False
