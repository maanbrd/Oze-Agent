from shared.behavior.client_field_update import (
    is_explicit_note_request,
    parse_client_field_update,
)


def test_email_reply_is_crm_field_update_not_note():
    parsed = parse_client_field_update("email zbigniew.borek@tlen.pl")

    assert parsed is not None
    assert parsed.updates == {"Email": "zbigniew.borek@tlen.pl"}
    assert is_explicit_note_request("email zbigniew.borek@tlen.pl") is False


def test_source_reply_is_crm_field_update():
    parsed = parse_client_field_update("źródło pozyskania D2D")

    assert parsed is not None
    assert parsed.updates == {"Źródło pozyskania": "D2D"}


def test_phone_address_and_product_are_normalized_fields():
    assert parse_client_field_update("telefon 525 225 242").updates == {
        "Telefon": "525225242"
    }
    assert parse_client_field_update("adres Czeska 20D").updates == {
        "Adres": "Czeska 20D"
    }
    assert parse_client_field_update("produkt fotowoltaika plus magazyn energii").updates == {
        "Produkt": "PV + Magazyn energii"
    }


def test_explicit_note_marker_is_not_field_update():
    assert parse_client_field_update("notatka: dach od południa") is None
    assert is_explicit_note_request("notatka: dach od południa") is True
    assert is_explicit_note_request("dopisz notatkę: dach od południa") is True
