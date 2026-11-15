"""
Centralized Application Logging Utility
Configures console and file-based logging with graceful error handling and no leak of sensitive data.
"""

import logging
import sys
from config import LOG_PATH


def setup_logger(name: str = "bmi_tracker") -> logging.Logger:
    """Initialize and return a configured logger instance."""
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)

    formatter = logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Console Handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.INFO)
    logger.addHandler(console_handler)

    # File Handler
    try:
        file_handler = logging.FileHandler(LOG_PATH, encoding="utf-8")
        file_handler.setFormatter(formatter)
        file_handler.setLevel(logging.INFO)
        logger.addHandler(file_handler)
    except Exception as e:
        logger.warning(f"Failed to initialize file logger: {e}")

    return logger


# Global logger instance
logger = setup_logger()
