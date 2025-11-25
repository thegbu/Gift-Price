"""Logging configuration with console and rotating file handlers."""
import logging
from logging.handlers import RotatingFileHandler
import sys


def setup_logging() -> None:
    """
    Sets up logging to console (INFO+) and rotating file (ERROR+).
    This function is idempotent and can be called multiple times safely.
    """
    logger = logging.getLogger()
    if logger.hasHandlers():
        return

    logger.setLevel(logging.INFO)

    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s (%(filename)s:%(lineno)d)'
    )

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    file_handler = RotatingFileHandler('vps_errors.log', maxBytes=2*1024*1024, backupCount=5, encoding='utf-8')
    file_handler.setLevel(logging.ERROR)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)