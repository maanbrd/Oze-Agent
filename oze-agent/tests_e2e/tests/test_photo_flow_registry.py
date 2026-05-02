"""Registry tests for the opt-in photo flow E2E scenario."""

from tests_e2e.scenarios._base import SCENARIOS, list_categories


def test_photo_flow_smoke_registered():
    assert "photo_flow_smoke" in SCENARIOS


def test_photo_flow_category_exists():
    assert "photo_flow" in list_categories()


def test_photo_flow_smoke_is_opt_in():
    scenario = SCENARIOS["photo_flow_smoke"]
    assert scenario.category == "photo_flow"
    assert scenario.default_in_run is False
