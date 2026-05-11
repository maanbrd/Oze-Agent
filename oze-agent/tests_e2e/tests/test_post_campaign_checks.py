"""Pure tests for post-campaign app smoke configuration."""

from tests_e2e import post_campaign_checks as checks


def test_post_campaign_cli_accepts_photo_and_offer_run_counts():
    args = checks._parse_args([
        "--photo-runs",
        "3",
        "--offer-runs",
        "2",
        "--report",
        "/tmp/report.md",
    ])

    assert args.photo_runs == 3
    assert args.offer_runs == 2
    assert args.report == "/tmp/report.md"


def test_offer_runs_require_controlled_recipient(monkeypatch):
    args = checks._parse_args(["--photo-runs", "0", "--offer-runs", "1"])
    monkeypatch.delenv(checks.OFFER_RECIPIENT_ENV, raising=False)

    error = checks.validate_post_campaign_args(args)

    assert error == f"{checks.OFFER_RECIPIENT_ENV} is required when --offer-runs > 0"


def test_zero_runs_are_rejected():
    args = checks._parse_args(["--photo-runs", "0", "--offer-runs", "0"])

    error = checks.validate_post_campaign_args(args)

    assert error == "at least one post-campaign app run is required"
