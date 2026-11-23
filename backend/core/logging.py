"""Structured logging setup with sensitive-data scrubbing."""

from __future__ import annotations

import logging
import re
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path


PASSWORD_MASK_PATTERN = re.compile(
    r"(password|passwd|secret|token|authorization)\s*[:=]\s*['\"]?([^'\"\s,&]+)",
    re.IGNORECASE,
)
RTSP_CRED_PATTERN = re.compile(r"(rtsp://[^:\s/]+:)([^@\s/]+)(@)", re.IGNORECASE)


class SensitiveDataFilter(logging.Filter):
    """Redacts passwords, tokens, and RTSP credentials from log records."""

    def filter(self, record: logging.LogRecord) -> bool:
        msg = record.getMessage()
        scrubbed = PASSWORD_MASK_PATTERN.sub(r"\1=***REDACTED***", msg)
        scrubbed = RTSP_CRED_PATTERN.sub(r"\1***REDACTED***\3", scrubbed)
        if scrubbed != msg:
            record.msg = scrubbed
            record.args = ()
        return True


def configure_logging(log_level: str = "INFO", log_file_path: str | None = None) -> logging.Logger:
    """Configure application-wide structured logging."""
    logger = logging.getLogger("cctv_assistant")
    level = getattr(logging, log_level.upper(), logging.INFO)
    logger.setLevel(level)

    if logger.handlers:
        return logger

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d | %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S%z",
    )
    sensitive_filter = SensitiveDataFilter()

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    console_handler.addFilter(sensitive_filter)
    logger.addHandler(console_handler)

    if log_file_path:
        try:
            file_path = Path(log_file_path)
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_handler = RotatingFileHandler(
                file_path, maxBytes=5 * 1024 * 1024, backupCount=3, encoding="utf-8"
            )
            file_handler.setLevel(level)
            file_handler.setFormatter(formatter)
            file_handler.addFilter(sensitive_filter)
            logger.addHandler(file_handler)
        except OSError:
            logger.warning("Could not initialize file logging at %s", log_file_path)

    return logger


def get_logger(name: str = "cctv_assistant") -> logging.Logger:
    """Return a named child logger under cctv_assistant."""
    base = logging.getLogger("cctv_assistant")
    if not base.handlers:
        configure_logging()
    if name == "cctv_assistant":
        return base
    return base.getChild(name)

