"""Ready-offer numbering helpers."""


def _ready_sort_key(template: dict) -> tuple[int, str]:
    sort_order = template.get("sort_order")
    try:
        order = int(sort_order)
    except (TypeError, ValueError):
        order = 1_000_000
    return order, str(template.get("created_at") or template.get("id") or "")


def list_ready_with_numbers(templates: list[dict]) -> list[dict]:
    ready = [t for t in templates if t.get("status") == "ready"]
    numbered: list[dict] = []
    for number, template in enumerate(sorted(ready, key=_ready_sort_key), start=1):
        item = dict(template)
        item["number"] = number
        numbered.append(item)
    return numbered


def get_ready_offer_by_number(templates: list[dict], number: int) -> dict | None:
    for item in list_ready_with_numbers(templates):
        if item["number"] == number:
            return item
    return None
