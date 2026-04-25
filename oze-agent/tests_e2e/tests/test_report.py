"""Unit tests for tests_e2e.report — pure stdlib, no Telegram, no Telethon."""

from datetime import datetime, timedelta, timezone

import pytest

from tests_e2e.report import CheckResult, ScenarioResult, write_report


def _ts(offset: int = 0) -> datetime:
    base = datetime(2026, 4, 24, 7, 0, 0, tzinfo=timezone.utc)
    return base + timedelta(seconds=offset)


# ── ScenarioResult.passed semantics ──────────────────────────────────────────


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


def test_blocker_check_marks_scenario_blocker():
    r = ScenarioResult(scenario_name="x", started_at=_ts())
    r.add("a", True)
    r.add_blocker("auth", "no bot reply")
    assert r.has_blocker is True
    assert r.verdict() == "BLOCKER"


# ── Tag semantics ────────────────────────────────────────────────────────────


def test_check_default_tag_pass_when_ok():
    c = CheckResult(name="x", passed=True)
    assert c.tag == "pass"


def test_check_auto_tag_fail_when_not_ok():
    # Default tag for failed check should auto-promote to "fail".
    c = CheckResult(name="x", passed=False)
    assert c.tag == "fail"


def test_check_explicit_known_drift_tag_does_not_auto_promote():
    c = CheckResult(name="x", passed=False, tag="known_drift", doc_ref="spec §3")
    assert c.tag == "known_drift"
    assert c.doc_ref == "spec §3"


def test_check_invalid_tag_raises():
    with pytest.raises(ValueError):
        CheckResult(name="x", passed=True, tag="weirdo")  # type: ignore[arg-type]


def test_known_drift_does_not_block_scenario_pass():
    r = ScenarioResult(scenario_name="x", started_at=_ts())
    r.add("ok_check", True)
    r.add_known_drift("docs_says_emoji_X", "code emits no emoji", doc_ref="spec_v5 §3")
    assert r.passed is True
    assert r.verdict() == "PASS"


def test_expected_fail_tag_does_not_block_scenario_pass():
    r = ScenarioResult(scenario_name="post_mvp_check", started_at=_ts())
    r.add("rejected_correctly", True)
    r.add(
        "edit_client_was_mutating", False,
        detail="POST-MVP path returned post-MVP reply, regression locked here",
        tag="expected_fail",
    )
    assert r.passed is True


def test_fail_tag_blocks_scenario():
    r = ScenarioResult(scenario_name="x", started_at=_ts())
    r.add("ok", True)
    r.add("regression", False, "this is bad")
    assert r.passed is False


# ── Markdown rendering ───────────────────────────────────────────────────────


def test_write_report_overall_pass_header(tmp_path):
    r = ScenarioResult(scenario_name="demo", started_at=_ts(), ended_at=_ts(5))
    r.add("check_one", True)
    path = tmp_path / "e2e.md"
    write_report([r], str(path))
    text = path.read_text(encoding="utf-8")
    assert text.startswith("# OZE-Agent E2E Report ✅")
    assert "**Overall:** PASS" in text


def test_write_report_overall_fail_with_mix(tmp_path):
    ok = ScenarioResult(scenario_name="s1", started_at=_ts(), ended_at=_ts(1))
    ok.add("a", True)
    bad = ScenarioResult(scenario_name="s2", started_at=_ts(), ended_at=_ts(1))
    bad.add("a", False, "boom")
    path = tmp_path / "e2e.md"
    write_report([ok, bad], str(path))
    text = path.read_text(encoding="utf-8")
    assert "# OZE-Agent E2E Report ❌" in text
    assert "**Overall:** FAIL" in text
    # New format: per-scenario name in code-tick + verdict marker
    assert "`s1`" in text and "PASS" in text
    assert "`s2`" in text and "FAIL" in text
    assert "boom" in text


def test_write_report_blocker_overrides_overall(tmp_path):
    r = ScenarioResult(scenario_name="auth", started_at=_ts(), ended_at=_ts(1))
    r.add_blocker("get_me", "auth expired")
    path = tmp_path / "e2e.md"
    write_report([r], str(path))
    text = path.read_text(encoding="utf-8")
    assert "# OZE-Agent E2E Report 🛑" in text
    assert "**Overall:** BLOCKER" in text
    assert "## 🛑 Blockers" in text


def test_write_report_known_drift_in_drift_section(tmp_path):
    r = ScenarioResult(scenario_name="cancel_text", started_at=_ts(), ended_at=_ts(1))
    r.add("got_anulowane_substring", True)
    r.add_known_drift(
        "exact_emoji_match",
        "spec says '🫡 Anulowane.', code emits '⚠️ Anulowane.'",
        doc_ref="agent_behavior_spec_v5.md §2.R1",
    )
    path = tmp_path / "e2e.md"
    write_report([r], str(path))
    text = path.read_text(encoding="utf-8")
    assert "## ⚠️ Known drifts (PASS but log)" in text
    assert "agent_behavior_spec_v5.md §2.R1" in text
    # Scenario itself is still PASS
    assert "**Overall:** PASS" in text


def test_write_report_escapes_pipe_in_detail(tmp_path):
    r = ScenarioResult(scenario_name="s1", started_at=_ts())
    r.add("pipe_test", False, "a | b")
    path = tmp_path / "e2e.md"
    write_report([r], str(path))
    text = path.read_text(encoding="utf-8")
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


def test_write_report_summary_counts_by_tag(tmp_path):
    r = ScenarioResult(scenario_name="multi", started_at=_ts())
    r.add("ok", True)
    r.add_known_drift("drift", "something", doc_ref="x")
    r.add("ef", False, tag="expected_fail")
    path = tmp_path / "e2e.md"
    write_report([r], str(path))
    text = path.read_text(encoding="utf-8")
    assert "pass=1" in text
    assert "known_drift=1" in text
    assert "expected_fail=1" in text


def test_write_report_categorizes_scenario_by_tag_in_section(tmp_path):
    """Scenarios with different shapes go to different sections."""
    blocker = ScenarioResult(scenario_name="b1", started_at=_ts(), ended_at=_ts(1))
    blocker.add_blocker("infra", "down")
    fail = ScenarioResult(scenario_name="f1", started_at=_ts(), ended_at=_ts(1))
    fail.add("regression", False)
    drift = ScenarioResult(scenario_name="d1", started_at=_ts(), ended_at=_ts(1))
    drift.add("ok", True)
    drift.add_known_drift("name", "deet", doc_ref="ref")
    clean = ScenarioResult(scenario_name="c1", started_at=_ts(), ended_at=_ts(1))
    clean.add("ok", True)
    path = tmp_path / "e2e.md"
    write_report([blocker, fail, drift, clean], str(path))
    text = path.read_text(encoding="utf-8")
    sections = ["## 🛑 Blockers", "## ❌ Fails",
                "## ⚠️ Known drifts (PASS but log)", "## ✅ Clean PASS"]
    indexes = [text.index(s) for s in sections]
    # Sections must appear in severity order: blockers → fails → drifts → clean.
    assert indexes == sorted(indexes)


# ── Backwards-compat scaffolding (existing scenario debug_brief uses .add(name, ok)) ─


def test_existing_two_arg_add_still_works():
    r = ScenarioResult(scenario_name="legacy", started_at=_ts())
    r.add("name", True)
    r.add("name2", False, "detail")
    assert r.checks[0].tag == "pass"
    assert r.checks[1].tag == "fail"
