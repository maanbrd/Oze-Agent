from shared.offers.validation import validate_offer_template, has_pdf_minimum


def test_ready_pv_offer_requires_pv_components():
    template = {
        "name": "PV 6 kWp",
        "product_type": "PV",
        "price_net_pln": 30000,
        "vat_rate": 8,
        "pv_power_kwp": 6,
        "panel_brand": "Jinko",
        "panel_model": "Tiger Neo",
        "inverter_brand": "Huawei",
    }

    result = validate_offer_template(template)

    assert not result.is_valid
    assert "falownik model" in " ".join(result.errors).lower()


def test_ready_storage_offer_requires_storage_components():
    template = {
        "name": "Magazyn 10 kWh",
        "product_type": "Magazyn energii",
        "price_net_pln": 25000,
        "vat_rate": 23,
        "storage_capacity_kwh": 10,
        "storage_brand": "BYD",
        "storage_model": "HVS",
    }

    result = validate_offer_template(template)

    assert result.is_valid
    assert result.errors == []


def test_ready_hybrid_offer_requires_pv_and_storage_fields():
    template = {
        "name": "PV plus magazyn",
        "product_type": "PV + Magazyn energii",
        "price_net_pln": 65000,
        "vat_rate": 8,
        "pv_power_kwp": 8,
        "panel_brand": "Jinko",
        "panel_model": "Tiger Neo",
        "inverter_brand": "Huawei",
        "inverter_model": "SUN2000",
        "storage_capacity_kwh": 10,
        "storage_brand": "BYD",
        "storage_model": "HVS",
    }

    assert validate_offer_template(template).is_valid


def test_pdf_preview_minimum_is_less_strict_than_ready_validation():
    template = {
        "name": "Robocza wycena",
        "product_type": "PV",
        "price_net_pln": 30000,
        "vat_rate": 8,
    }

    assert has_pdf_minimum(template)
    assert not validate_offer_template(template).is_valid
