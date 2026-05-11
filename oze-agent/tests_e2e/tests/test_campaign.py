"""Pure tests for the smoke E2E campaign planner."""

import pytest

from tests_e2e import campaign


def test_requested_matrix_records_written_plan_total():
    assert campaign.requested_total() == 540


def test_normalized_matrix_hits_campaign_target():
    assert campaign.normalized_total() == 500


def test_build_campaign_units_has_expected_driver_counts():
    units = campaign.build_campaign_units()
    assert len(units) == 500
    assert len(campaign.telethon_units(units)) == 420
    assert len(campaign.external_units(units)) == 80


def test_campaign_external_units_cover_drive_and_gmail():
    units = campaign.external_units(campaign.build_campaign_units())
    buckets = {u.bucket for u in units}
    assert {"drive_photo_flow", "offer_gmail_flow"}.issubset(buckets)
    surfaces = {surface for u in units for surface in u.surfaces}
    assert {"drive", "gmail", "sheets", "telegram"}.issubset(surfaces)


def test_realistic_scenarios_are_explicit():
    assert campaign.REALISTIC_SCENARIOS == (
        "realistic_add_client_sheets_save",
        "realistic_add_meeting_calendar_sheets_save",
        "realistic_show_day_plan_after_meeting",
    )


def test_render_plan_mentions_normalization_and_gates():
    text = campaign.render_plan(campaign.build_campaign_units())
    assert "Requested matrix total: 540" in text
    assert "Normalized campaign total: 500" in text
    assert "--confirm-test-environment" in text
    assert campaign.DASHBOARD_URL_ENV in text
    assert campaign.OFFER_RECIPIENT_ENV in text


def test_pilot_limit_is_capped_at_50():
    assert campaign.validate_pilot_limit(50) == 50
    with pytest.raises(ValueError):
        campaign.validate_pilot_limit(51)


def test_full_campaign_gate_is_explicit_cli_confirmation():
    args = campaign._parse_args(["--telethon-full", "--confirm-test-environment"])
    assert args.telethon_full is True
    assert args.confirm_test_environment is True


def test_cleanup_report_safety_gate():
    assert campaign._cleanup_is_safe({"cleanup_safe": True}) is True
    assert campaign._cleanup_is_safe({"cleanup_safe": False}) is False
    assert campaign._cleanup_is_safe({"cleanup_error": "timeout"}) is False


def test_campaign_footer_keeps_app_and_connector_evidence_separate():
    units = campaign.telethon_units(campaign.build_campaign_units())[:2]
    omitted = campaign.external_units(campaign.build_campaign_units())

    footer = campaign._campaign_footer(units, omitted)

    assert "## Post-app Results" in footer
    assert "## Codex Connector Evidence" in footer
    assert "## Dashboard Evidence" in footer
    assert "Post-app checks are required for Drive/Gmail PASS." in footer
