"""
This module provides logging configuration with support for colored console output,
file rotation, and JSON formatting.
"""

import json
import logging
import logging.handlers
import uuid
from datetime import datetime
from pathlib import Path
from types import TracebackType
from typing import Any, Dict, Optional, Tuple, cast

import yaml
from termcolor import colored


class ColoredFormatter(logging.Formatter):
    """
    This class provides a formatter for logging output with colors.
    """

    COLORS = {
        "WARNING": "yellow",
        "INFO": "white",
        "DEBUG": "blue",
        "CRITICAL": "red",
        "ERROR": "red",
    }

    def format(self, record: logging.LogRecord) -> str:
        """
        Formats the log record with colors based on the log level.

        Args:
            record: The log record to format.

        Returns:
            The formatted log record.
        """
        colored_record = record
        levelname = record.levelname
        if levelname in self.COLORS:
            colored_levelname = colored(levelname, self.COLORS[levelname])
            colored_record.levelname = colored_levelname
        return super().format(colored_record)


class JsonFormatter(logging.Formatter):
    """
    This class provides a formatter for JSON logging output.
    """

    def __init__(self) -> None:
        super().__init__()
        self.correlation_id: Optional[str] = None

    def format(self, record: logging.LogRecord) -> str:
        """
        Formats the log record as JSON.

        Args:
            record: The log record to format.

        Returns:
            The formatted log record as JSON string.
        """
        log_data: Dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "correlation_id": getattr(record, "correlation_id", None),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add exception info if present
        if record.exc_info:
            # record.exc_info may be Tuple[type|None, BaseException|None, TracebackType|None]

            ExcInfo = Tuple[type, BaseException, Optional[TracebackType]]
            exc_info = cast(ExcInfo, record.exc_info)
            exc_type, exc_value, exc_tb = exc_info
            log_data["exception"] = {
                "type": exc_type.__name__,
                "message": str(exc_value),
                "traceback": self.formatException(exc_info),
            }

        # Add extra fields if present
        if hasattr(record, "extra"):
            log_data.update(record.extra)

        return json.dumps(log_data)


def get_log_config() -> Dict[str, Any]:
    """
    Get logging configuration from config file.

    Returns:
        Dict containing logging configuration.
    """
    try:
        config_path = (
            Path(__file__).parent.parent.parent / "config" / "config.yml"
        )
        with open(config_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)

        return config.get(
            "logging",
            {
                "level": "INFO",
                "format": "%(asctime)s - %(levelname)s - %(message)s",
                "file": {
                    "enabled": False,
                    "path": "logs/app.log",
                    "max_size": 10485760,  # 10MB
                    "backup_count": 5,
                    "format": "json",
                },
            },
        )
    except Exception as e:
        print(f"Error loading log config: {e}")
        return {
            "level": "INFO",
            "format": "%(asctime)s - %(levelname)s - %(message)s",
            "file": {
                "enabled": False,
                "path": "logs/app.log",
                "max_size": 10485760,
                "backup_count": 5,
                "format": "json",
            },
        }


def setup_logging() -> None:
    """
    Set up logging configuration with console and file handlers.
    """
    config = get_log_config()
    log_level = getattr(logging, config["level"].upper())

    # Create logger
    logger = logging.getLogger()
    logger.setLevel(log_level)

    # Remove existing handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)

    # Create console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_formatter = ColoredFormatter(config["format"])
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    # Suppress selenium logs (at least just show errors)
    for name in (
        "selenium.webdriver.common.driver_finder",  # driver finder
        "selenium.webdriver.remote.remote_connection",  # HTTP client logs from selenium
        "selenium.webdriver.firefox.service",  # GeckoDriver service logs
        "selenium.webdriver.common.service",  # shared service base
        "urllib3.connectionpool",  # low‑level HTTP debug
        "urllib3",  # bare urllib3 logs
    ):
        lg = logging.getLogger(name)
        lg.setLevel(logging.ERROR)
        lg.propagate = False

    # Create file handler if enabled
    if config["file"]["enabled"]:
        # Create logs directory if it doesn't exist
        log_path = Path(config["file"]["path"])
        log_path.parent.mkdir(parents=True, exist_ok=True)

        # Create rotating file handler
        file_handler = logging.handlers.RotatingFileHandler(
            filename=log_path,
            maxBytes=config["file"]["max_size"],
            backupCount=config["file"]["backup_count"],
        )
        file_handler.setLevel(log_level)

        file_formatter: logging.Formatter
        # Use JSON formatter for file output
        if config["file"]["format"].lower() == "json":
            file_formatter = JsonFormatter()
        else:
            file_formatter = logging.Formatter(config["format"])

        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)


class CorrelationFilter(logging.Filter):
    """Filter to add correlation ID to log records."""

    def __init__(self):
        """Initialize the filter."""
        super().__init__()
        self.correlation_id: Optional[str] = None

    def filter(self, record: logging.LogRecord) -> bool:
        """
        Add correlation ID to the log record.

        Args:
            record: The log record to filter

        Returns:
            True to allow the record through
        """
        if self.correlation_id:
            record.correlation_id = self.correlation_id
        return True


def get_correlation_id() -> Optional[str]:
    """
    Get the current correlation ID from the logging context.

    Returns:
        The current correlation ID or None if not set.
    """
    for f in logging.getLogger().filters:
        if isinstance(f, CorrelationFilter):
            return f.correlation_id
    return None


def set_correlation_id(correlation_id: Optional[str] = None) -> str:
    """
    Set the correlation ID in the logging context.

    Args:
        correlation_id: The correlation ID to set. If None, a new UUID is generated.

    Returns:
        The set correlation ID.
    """
    if correlation_id is None:
        correlation_id = str(uuid.uuid4())
    for f in logging.getLogger().filters:
        if isinstance(f, CorrelationFilter):
            f.correlation_id = correlation_id
            break
    return correlation_id
