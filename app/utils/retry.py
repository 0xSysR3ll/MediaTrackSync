"""
This module provides retry functionality with exponential backoff.
"""

import logging
import random
import time
from functools import wraps
from pathlib import Path
from typing import Any, Callable, Optional, Tuple, Type, Union

import yaml

logger = logging.getLogger(__name__)


def get_retry_config() -> dict:
    """
    Get retry configuration from config file.

    Returns:
        dict: Retry configuration.
    """
    try:
        config_path = (
            Path(__file__).parent.parent.parent / "config" / "config.yml"
        )
        with open(config_path, "r") as f:
            config = yaml.safe_load(f)

        return config.get(
            "retry",
            {
                "max_retries": 3,
                "initial_delay": 1,
                "max_delay": 10,
                "backoff_factor": 2,
                "jitter": 0.1,
            },
        )
    except Exception as e:
        logger.warning(f"Error loading retry config: {e}")
        return {
            "max_retries": 3,
            "initial_delay": 1,
            "max_delay": 10,
            "backoff_factor": 2,
            "jitter": 0.1,
        }


def retry(
    exceptions: Union[
        Type[Exception], Tuple[Type[Exception], ...]
    ] = Exception,
    max_retries: Optional[int] = None,
    initial_delay: Optional[float] = None,
    max_delay: Optional[float] = None,
    backoff_factor: Optional[float] = None,
    jitter: Optional[float] = None,
) -> Callable:
    """
    Retry decorator with exponential backoff.

    Args:
        exceptions: Exception(s) to catch and retry on.
        max_retries: Maximum number of retries.
        initial_delay: Initial delay between retries in seconds.
        max_delay: Maximum delay between retries in seconds.
        backoff_factor: Exponential backoff factor.
        jitter: Jitter factor (0-1) to add randomness to delays.

    Returns:
        Callable: Decorated function.
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Get retry configuration
            config = get_retry_config()
            max_retries_ = max_retries or config["max_retries"]
            initial_delay_ = initial_delay or config["initial_delay"]
            max_delay_ = max_delay or config["max_delay"]
            backoff_factor_ = backoff_factor or config["backoff_factor"]
            jitter_ = jitter or config["jitter"]

            # Initialize retry variables
            retry_count = 0
            delay = initial_delay_

            while True:
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    retry_count += 1
                    if retry_count > max_retries_:
                        logger.error(
                            f"Max retries ({max_retries_}) exceeded for {func.__name__}: {str(e)}"
                        )
                        raise

                    # Calculate delay with exponential backoff and jitter
                    delay = min(delay * backoff_factor_, max_delay_)
                    jitter_amount = delay * jitter_ * random.uniform(-1, 1)
                    sleep_time = delay + jitter_amount

                    logger.warning(
                        f"Retry {retry_count}/{max_retries_} for {func.__name__} "
                        f"after {sleep_time:.2f}s: {str(e)}"
                    )
                    time.sleep(sleep_time)

        return wrapper

    return decorator
