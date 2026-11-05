"""Structured logging for Carti Backend."""

import logging
import sys
from server.app.core.config import settings


def setup_logging():
    """Configure structured logging format for Carti."""
    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)

    formatter = logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    # Avoid duplicate handlers if reloaded
    if not root_logger.handlers:
        root_logger.addHandler(handler)
    else:
        root_logger.handlers[0] = handler

    # Quiet external noisy libraries
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)


logger = logging.getLogger("carti")
