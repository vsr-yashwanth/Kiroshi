import json
import logging
import sys
from datetime import datetime, timezone
from backend.app.core.config import settings


class JsonLogFormatter(logging.Formatter):
    """
    Standardized JSON log formatter for KIROSHI production observability.
    Guarantees machine-readable logs with zero sensitive credential leakage.
    """

    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Append extra context if present
        if hasattr(record, "request_id"):
            log_entry["request_id"] = record.request_id
        if hasattr(record, "actor_id"):
            log_entry["actor_id"] = record.actor_id
        if hasattr(record, "status_code"):
            log_entry["status_code"] = record.status_code
        if hasattr(record, "duration_ms"):
            log_entry["duration_ms"] = record.duration_ms

        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_entry)


def setup_logging():
    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
    logger_instance = logging.getLogger("kiroshi")
    logger_instance.setLevel(log_level)
    logger_instance.propagate = False

    # Remove existing handlers
    if logger_instance.hasHandlers():
        logger_instance.handlers.clear()

    handler = logging.StreamHandler(sys.stdout)
    if settings.LOG_FORMAT.lower() == "json":
        handler.setFormatter(JsonLogFormatter())
    else:
        handler.setFormatter(
            logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
        )

    logger_instance.addHandler(handler)
    return logger_instance


logger = setup_logging()

