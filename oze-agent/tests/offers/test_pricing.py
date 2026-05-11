from shared.offers.pricing import calculate_price, format_pln


def test_calculate_gross_price_with_8_percent_vat():
    result = calculate_price(net_price_pln=50000, vat_rate=8)

    assert result.net_price_pln == 50000
    assert result.gross_price_pln == 54000
    assert result.client_price_pln == 54000
    assert result.subsidy_amount_pln is None


def test_calculate_client_price_after_subsidy():
    result = calculate_price(net_price_pln=50000, vat_rate=23, subsidy_amount_pln=20000)

    assert result.gross_price_pln == 61500
    assert result.client_price_pln == 41500
    assert result.subsidy_amount_pln == 20000


def test_subsidy_never_reduces_price_below_zero():
    result = calculate_price(net_price_pln=10000, vat_rate=8, subsidy_amount_pln=999999)

    assert result.gross_price_pln == 10800
    assert result.client_price_pln == 0


def test_format_pln_uses_full_pln_without_cents():
    assert format_pln(61500.49) == "61 500 PLN"
    assert format_pln(61500.5) == "61 500 PLN"
