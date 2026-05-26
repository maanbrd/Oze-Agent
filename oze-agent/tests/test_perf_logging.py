import logging

from shared.perf import configure_perf_aggregator_for_tests, log_duration, reset_perf_aggregator_for_tests


def test_log_duration_records_operation_and_ms_without_labels(caplog):
    logger = logging.getLogger("tests.perf")

    with caplog.at_level(logging.INFO, logger="tests.perf"):
        with log_duration(logger, "google.sheets.get_client_by_row"):
            pass

    assert len(caplog.records) == 1
    record = caplog.records[0]
    assert record.message.startswith("perf op=google.sheets.get_client_by_row duration_ms=")
    assert "Jan" not in record.message
    assert "row=" not in record.message
    assert "@example" not in record.message
    assert "600" not in record.message


def test_log_duration_emits_percentile_summary_without_pii_labels(caplog):
    logger = logging.getLogger("tests.perf.summary")
    reset_perf_aggregator_for_tests()
    configure_perf_aggregator_for_tests(sample_threshold=2, interval_seconds=3600)

    try:
        with caplog.at_level(logging.INFO, logger="tests.perf.summary"):
            with log_duration(logger, "google.sheets.get_all_clients"):
                pass
            with log_duration(logger, "google.sheets.get_all_clients"):
                pass
    finally:
        reset_perf_aggregator_for_tests()

    summaries = [record.message for record in caplog.records if record.message.startswith("perf_summary ")]
    assert len(summaries) == 1
    summary = summaries[0]
    assert "op=google.sheets.get_all_clients" in summary
    assert "p50_ms=" in summary
    assert "p95_ms=" in summary
    assert "p99_ms=" in summary
    assert "max_ms=" in summary
    assert "Jan" not in summary
    assert "@example" not in summary
