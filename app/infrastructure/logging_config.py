"""
Logging configuration.
Configures console, file and Logfire handlers. Call after configure_logfire().
"""

import logging
import sys
from pathlib import Path

import logfire

from app.infrastructure.config import Settings


def setup_logging(settings: Settings) -> None:
    """
    Configure logging: format, handlers (stdout, optional file, Logfire), and basicConfig.
    When TESTING is True, file handler is skipped to avoid polluting logs.
    """
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    formatter = logging.Formatter(log_format)

    handlers: list[logging.Handler] = [
        logging.StreamHandler(sys.stdout),
        logfire.LogfireLoggingHandler(),
    ]

    if not settings.TESTING:
        Path("logs").mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler("logs/app.log")
        file_handler.setFormatter(formatter)
        handlers.append(file_handler)

    for h in handlers:
        h.setFormatter(formatter)
    logging.basicConfig(level=logging.INFO, format=log_format, handlers=handlers)
