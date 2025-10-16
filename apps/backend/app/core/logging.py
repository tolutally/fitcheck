import logging
import logging.config
from typing import Dict, Any

from .config import settings

def setup_logging_config() -> Dict[str, Any]:
    """Configure Fitscore's logging system"""
    return {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                "format": "[%(asctime)s] %(levelname)s in %(module)s: %(message)s",
            },
            "access": {
                "format": "%(message)s",
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "default",
                "stream": "ext://sys.stdout",
            },
            "error_file": {
                "class": "logging.handlers.RotatingFileHandler",
                "formatter": "default",
                "filename": "logs/error.log",
                "maxBytes": 10485760,  # 10MB
                "backupCount": 5,
                "level": "ERROR",
            },
            "access_file": {
                "class": "logging.handlers.RotatingFileHandler",
                "formatter": "access",
                "filename": "logs/access.log",
                "maxBytes": 10485760,  # 10MB
                "backupCount": 5,
            },
        },
        "loggers": {
            "fitscore": {
                "level": settings.LOG_LEVEL,
                "handlers": ["console", "error_file"],
                "propagate": False,
            },
            "fitscore.access": {
                "level": "INFO",
                "handlers": ["access_file"],
                "propagate": False,
            },
        },
        "root": {
            "level": "INFO",
            "handlers": ["console"],
        },
    }

def init_logging():
    """Initialize Fitscore's logging system"""
    config = setup_logging_config()
    logging.config.dictConfig(config)

    # Create a logger for the application
    logger = logging.getLogger("fitscore")
    logger.info(f"Fitscore starting in {settings.ENVIRONMENT} mode")