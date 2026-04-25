"""Runner-level tests: scenario registry and selection parsing."""

import pytest

from tests_e2e import runner


def test_registry_contains_debug_brief():
    assert "debug_brief" in runner.SCENARIOS


def test_select_scenarios_defaults_to_all():
    selected = runner._select_scenarios([])
    assert {name for name, _ in selected} == set(runner.SCENARIOS)


def test_select_scenarios_rejects_unknown_name():
    with pytest.raises(SystemExit) as excinfo:
        runner._select_scenarios(["does_not_exist"])
    assert "does_not_exist" in str(excinfo.value)


def test_select_scenarios_returns_known():
    selected = runner._select_scenarios(["debug_brief"])
    assert [name for name, _ in selected] == ["debug_brief"]
