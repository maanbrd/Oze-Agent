"""Unit tests for tests_e2e.report — pure stdlib, no Telegram, no Telethon."""

from datetime import datetime, timedelta, timezone

from tests_e2e.report import CheckResult, ScenarioResult, write_report


def _ts(offset: int = 0) -> datetime:
    base = datetime(2026, 4, 24, 7, 0, 0, tzinfo=timezone.utc)
    return base + timedelta(seconds=offset)


def test_scenario_result_passed_requires_at_least_one_check():
    r = ScenarioResult(scenario_name="x", started_at=_ts())
    assert r.passed is False


def test_scenario_result_passed_true_when_all_checks_pass():
    r = ScenarioResult(scenario_name="x", started_at=_ts())
    r.add("a", True)
    r.add("b", True, "ok")
    assert r.passed is True
    assert r.verdict() == "PASS"


def test_scenario_result_passed_false_when_any_check_fails():
    r = ScenarioResult(scenario_name="x", started_at=_ts())
    r.add("a", True)
    r.add("b", False, "nope")
    assert r.passed is False
    assert r.verdict() == "FAIL"


def test_write_report_produces_overall_pass_header(tmp_path):
    r = ScenarioResult(scenario_name="demo", started_at=_ts(), ended_at=_ts(5))
    r.add("check_one", True)
    path = tmp_path / "e2e.md"
    write_report([r], str(path))
    text = path.read_text(encoding="utf-8")
    assert text.startswith("# OZE-Agent E2E Report ✅")
    assert "**Overall:** PASS" in text
    assert "**Passed:** 1 / 1" in text


def test_write_report_produces_overall_fail_with_mix(tmp_path):
    ok = ScenarioResult(scenario_name="s1", started_at=_ts(), ended_at=_ts(1))
    ok.add("a", True)
    bad = ScenarioResult(scenario_name="s2", started_at=_ts(), ended_at=_ts(1))
    bad.add("a", False, "boom")
    path = tmp_path / "e2e.md"
    write_report([ok, bad], str(path))
    text = path.read_text(encoding="utf-8")
    assert "# OZE-Agent E2E Report ❌" in text
    assert "**Overall:** FAIL" in text
    assert "**Passed:** 1 / 2" in text
    # Each scenario section should be rendered
    assert "s1 — PASS" in text
    assert "s2 — FAIL" in text
    assert "boom" in text


def test_write_report_escapes_pipe_in_detail(tmp_path):
    r = ScenarioResult(scenario_name="s1", started_at=_ts())
    r.add("pipe_test", False, "a | b")
    path = tmp_path / "e2e.md"
    write_report([r], str(path))
    text = path.read_text(encoding="utf-8")
    # Table column separator must not be broken by a bare pipe in detail.
    assert "a \\| b" in text


def test_write_report_includes_context_block(tmp_path):
    r = ScenarioResult(scenario_name="s1", started_at=_ts())
    r.add("a", True)
    r.context["first_run_message_count"] = 3
    path = tmp_path / "e2e.md"
    write_report([r], str(path))
    text = path.read_text(encoding="utf-8")
    assert "<details><summary>Context</summary>" in text
    assert "first_run_message_count: 3" in text


def test_check_result_defaults():
    c = CheckResult(name="x", passed=True)
    assert c.detail == ""
