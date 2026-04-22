import logging

from src.logging_utils import log_timing


def test_log_timing_logs_start_and_done(caplog):
    logger = logging.getLogger("test.logger")

    with caplog.at_level(logging.INFO):
        with log_timing(logger, "demo.event", request_id="abc123"):
            pass

    assert "demo.event.start request_id=abc123" in caplog.text
    assert "demo.event.done" in caplog.text
