from shared.offers.numbering import get_ready_offer_by_number, list_ready_with_numbers


def test_ready_offer_numbers_follow_current_manual_order():
    templates = [
        {"id": "draft", "status": "draft", "name": "Szkic", "sort_order": None},
        {"id": "b", "status": "ready", "name": "B", "sort_order": 20},
        {"id": "a", "status": "ready", "name": "A", "sort_order": 10},
    ]

    numbered = list_ready_with_numbers(templates)

    assert [(item["number"], item["id"]) for item in numbered] == [(1, "a"), (2, "b")]
    assert get_ready_offer_by_number(templates, 2)["id"] == "b"


def test_deleted_offer_number_is_reused_by_collapsed_list():
    templates = [
        {"id": "a", "status": "ready", "name": "A", "sort_order": 10},
        {"id": "c", "status": "ready", "name": "C", "sort_order": 30},
    ]

    assert get_ready_offer_by_number(templates, 2)["id"] == "c"
