import logging
import logging.config
from pathlib import Path

from config.config import settings


def configure_logging() -> None:
    """
    Configure application-wide logging handlers and formatters.

    Ensures the log directory exists before attaching file handlers.
    """
    handlers = {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "standard",
            "level": "INFO",
        }
    }

    if settings.LOG_DIR and settings.LOG_FILE:
        log_dir = Path(settings.LOG_DIR)
        log_dir.mkdir(parents=True, exist_ok=True)
        handlers["file"] = {
            "class": "logging.FileHandler",
            "formatter": "standard",
            "level": "INFO",
            "filename": str(log_dir / settings.LOG_FILE),
        }

    logging.config.dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "standard": {
                    "format": "%(asctime)s - %(levelname)s - %(message)s",
                }
            },
            "handlers": handlers,
            "root": {
                "handlers": list(handlers.keys()),
                "level": "INFO",
            },
        }
    )
    logging.getLogger(__name__).info("Logging configured")
