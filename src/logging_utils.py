import logging
import time
import uuid
from contextlib import contextmanager


def configure_logging() -> None:
    root_logger = logging.getLogger()
    if root_logger.handlers:
        return

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )


def new_request_id() -> str:
    return uuid.uuid4().hex[:12]


@contextmanager
def log_timing(logger: logging.Logger, event: str, **fields):
    started_at = time.perf_counter()
    logger.info("%s.start %s", event, _format_fields(fields))
    try:
        yield
    except Exception:
        duration_ms = int((time.perf_counter() - started_at) * 1000)
        logger.exception("%s.error duration_ms=%s %s", event, duration_ms, _format_fields(fields))
        raise
    else:
        duration_ms = int((time.perf_counter() - started_at) * 1000)
        logger.info("%s.done duration_ms=%s %s", event, duration_ms, _format_fields(fields))


def _format_fields(fields: dict) -> str:
    return " ".join(f"{key}={value}" for key, value in fields.items() if value is not None)
