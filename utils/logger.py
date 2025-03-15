"""
Logging configuration for PagePal application.
Sets up loggers for different modules.
"""

import logging
import sys
from pathlib import Path
from typing import Optional

from config import config


def setup_logger(
    name: str,
    log_level: int = None,
    log_file: Optional[Path] = None,
    log_format: Optional[str] = None,
) -> logging.Logger:
    """
    Set up and configure a logger.

    Args:
        name: Name of the logger
        log_level: Logging level (defaults to config.LOG_LEVEL)
        log_file: Path to log file (optional)
        log_format: Format for log messages (defaults to config.LOG_FORMAT)

    Returns:
        logging.Logger: Configured logger
    """
    # Use values from config if not specified
    if log_level is None:
        log_level = config.LOG_LEVEL

    if log_format is None:
        log_format = config.LOG_FORMAT

    if log_file is None and config.LOG_FILE:
        log_file = Path(config.LOG_FILE)

    logger = logging.getLogger(name)
    logger.setLevel(log_level)

    # Avoid adding handlers multiple times
    if not logger.handlers:
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(logging.Formatter(log_format))
        logger.addHandler(console_handler)

        # File handler (if specified)
        if log_file:
            # Create directory if it doesn't exist
            log_file.parent.mkdir(parents=True, exist_ok=True)
            file_handler = logging.FileHandler(log_file)
            file_handler.setFormatter(logging.Formatter(log_format))
            logger.addHandler(file_handler)

    return logger


# Create default logger for the application
app_logger = setup_logger("pagepal")

# Create loggers for different modules
bot_logger = setup_logger("pagepal.bot")
crawler_logger = setup_logger("pagepal.crawler")
db_logger = setup_logger("pagepal.db")
rag_logger = setup_logger("pagepal.rag")
