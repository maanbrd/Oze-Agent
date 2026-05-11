"""Pricing calculations for offer templates."""

from dataclasses import dataclass


@dataclass(frozen=True)
class PriceBreakdown:
    net_price_pln: int
    vat_rate: int
    gross_price_pln: int
    subsidy_amount_pln: int | None
    client_price_pln: int


def _whole_pln(value: int | float | str | None) -> int:
    if value in (None, ""):
        return 0
    return max(0, int(round(float(value))))


def calculate_price(
    net_price_pln: int | float | str,
    vat_rate: int | str,
    subsidy_amount_pln: int | float | str | None = None,
) -> PriceBreakdown:
    """Return net/gross/client price in full PLN.

    `client_price_pln` is the main price shown to the customer: gross price
    minus subsidy when subsidy was entered, otherwise gross price.
    """
    vat = int(vat_rate)
    if vat not in (8, 23):
        raise ValueError("VAT must be 8 or 23")

    net = _whole_pln(net_price_pln)
    gross = _whole_pln(net * (1 + vat / 100))
    subsidy = _whole_pln(subsidy_amount_pln) if subsidy_amount_pln not in (None, "") else None
    client_price = max(0, gross - subsidy) if subsidy is not None else gross
    return PriceBreakdown(
        net_price_pln=net,
        vat_rate=vat,
        gross_price_pln=gross,
        subsidy_amount_pln=subsidy,
        client_price_pln=client_price,
    )


def format_pln(value: int | float | str | None) -> str:
    amount = _whole_pln(value)
    return f"{amount:,}".replace(",", " ") + " PLN"
