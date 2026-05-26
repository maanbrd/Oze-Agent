import logging

from shared.perf import log_duration


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
