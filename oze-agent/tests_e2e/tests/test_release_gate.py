"""Release-gate tests for controlled production hardening."""

import subprocess

from tests_e2e import release_gate
from tests_e2e.scenarios._base import list_categories


def test_release_gate_categories_exist_in_registry():
    assert set(release_gate.RELEASE_GATE_CATEGORIES).issubset(set(list_categories()))


def test_release_gate_blocks_non_test_bot_without_override():
    findings = release_gate.validate_release_environment(
        bot_username="@OZEAgentProdBot",
        railway_service="bot-test",
        allow_prod_bot=False,
        include_offer_send=False,
        offer_recipient="",
    )

    assert findings.ok is False
    assert any("bot username" in item for item in findings.blockers)


def test_release_gate_blocks_non_test_railway_service_without_override():
    findings = release_gate.validate_release_environment(
        bot_username="@OZEAgentTestBot",
        railway_service="bot",
        allow_prod_bot=False,
        include_offer_send=False,
        offer_recipient="",
    )

    assert findings.ok is False
    assert any("Railway service" in item for item in findings.blockers)


def test_release_gate_requires_controlled_offer_recipient_for_offer_send():
    findings = release_gate.validate_release_environment(
        bot_username="@OZEAgentTestBot",
        railway_service="bot-test",
        allow_prod_bot=False,
        include_offer_send=True,
        offer_recipient="",
    )

    assert findings.ok is False
    assert any("TELEGRAM_E2E_OFFER_RECIPIENT" in item for item in findings.blockers)


def test_release_gate_commands_seed_fixtures_before_live_categories():
    commands = release_gate.build_release_gate_commands(report_dir="output/smoke/gate")
    rendered = [command.render() for command in commands]

    assert rendered[0] == "./tests_e2e/run_release_gate.sh pytest-tests"
    assert "./tests_e2e/run_release_gate.sh list" in rendered[1]
    assert any("run_release_gate.sh google-health" in item for item in rendered)
    assert any("run_release_gate.sh seed" in item for item in rendered)
    assert any("category mutating_core" in item for item in rendered)
    assert any("category photo_flow" in item for item in rendered)


def test_release_gate_commands_are_not_prod_deploy_commands():
    commands = release_gate.build_release_gate_commands(report_dir="output/smoke/gate")
    rendered = "\n".join(command.render() for command in commands)

    assert "railway up" not in rendered
    assert "git merge" not in rendered
    assert "git push" not in rendered


def test_release_gate_commands_use_wrapper_instead_of_raw_python():
    commands = release_gate.build_release_gate_commands(report_dir="output/smoke/gate")
    rendered = "\n".join(command.render() for command in commands)

    assert "./tests_e2e/run_release_gate.sh" in rendered
    assert " python3 -m " not in rendered


def test_release_gate_wrapper_forwards_options_to_release_gate_cli():
    completed = subprocess.run(
        ["./tests_e2e/run_release_gate.sh", "--commands-only"],
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0
    assert "Release gate commands" in completed.stdout
    assert "unknown release-gate command" not in completed.stderr


def test_mcp_release_gate_status_renderer_includes_blockers_and_commands():
    from tests_e2e.mcp_server import _render_release_gate_status

    findings = release_gate.validate_release_environment(
        bot_username="@WrongBot",
        railway_service="bot-test",
        allow_prod_bot=False,
        include_offer_send=False,
        offer_recipient="",
    )

    text = _render_release_gate_status(findings, report_dir="output/smoke/gate")

    assert "Release gate environment: BLOCKED" in text
    assert "BLOCKER:" in text
    assert "Release gate commands" in text
    assert "run_release_gate.sh google-health" in text
