"""
This module provides pytest fixtures and configuration.
"""

import sys
from pathlib import Path
from typing import Any, Dict, Generator

import pytest
import requests
import yaml

# Add the project root directory to Python path
PROJECT_ROOT = str(Path(__file__).parent.parent)
sys.path.insert(0, PROJECT_ROOT)


@pytest.fixture
def config_dir(tmp_path: Path) -> Path:
    """
    Create a temporary config directory.

    Args:
        tmp_path: Pytest's temporary directory fixture.

    Returns:
        Path to the temporary config directory.
    """
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    return config_dir


@pytest.fixture
def config_file(config_dir: Path) -> Path:
    """
    Create a temporary config file.

    Args:
        config_dir: Path to the config directory.

    Returns:
        Path to the temporary config file.
    """
    config = {
        "logging": {
            "level": "DEBUG",
            "format": "%(asctime)s - %(levelname)s - %(message)s",
            "file": {
                "enabled": True,
                "path": "logs/test.log",
                "max_size": 1048576,  # 1MB
                "backup_count": 2,
                "format": "json",
            },
        },
        "webhook": {
            "rate_limit": {"requests_per_minute": 60, "burst_size": 10},
        },
        "users": {
            "test_user": {
                "tvtime": {
                    "username": "test@example.com",
                    "password": "test-password",
                },
                "tracktv": {
                    "client_id": "test-client-id",
                    "client_secret": "test-client-secret",
                    "code": "test-auth-code",
                    "redirect_uri": "http://127.0.0.1:5000",
                },
            }
        },
        "retry": {
            "max_retries": 3,
            "initial_delay": 0.1,
            "max_delay": 1,
            "backoff_factor": 2,
            "jitter": 0.1,
        },
    }

    config_file = config_dir / "config.yml"
    with open(config_file, "w") as f:
        yaml.dump(config, f)

    return config_file


@pytest.fixture
def mock_config(monkeypatch: pytest.MonkeyPatch, config_file: Path) -> None:
    """
    Mock the config file path.

    Args:
        monkeypatch: Pytest's monkeypatch fixture.
        config_file: Path to the config file.
    """

    def mock_config_path(*args: Any, **kwargs: Any) -> Path:
        return config_file

    monkeypatch.setattr("app.utils.logger.get_log_config", mock_config_path)
    monkeypatch.setattr("app.utils.retry.get_retry_config", mock_config_path)


class MockResponse:
    """Mock response object that mimics requests.Response."""

    def __init__(
        self,
        status_code: int,
        json_data: Dict[str, Any] = None,
        text: str = None,
    ):
        self.status_code = status_code
        self._json_data = json_data
        self._text = text

    def json(self) -> Dict[str, Any]:
        """Return the JSON data."""
        return self._json_data or {}

    @property
    def text(self) -> str:
        """Return the text data."""
        return self._text or ""

    def raise_for_status(self) -> None:
        """Raise an HTTPError if the status code is not 2xx."""
        if 400 <= self.status_code < 600:
            raise requests.exceptions.HTTPError(
                f"{self.status_code} Error: {self.text}", response=self
            )


@pytest.fixture
def mock_requests(
    monkeypatch: pytest.MonkeyPatch,
) -> Generator[Dict[str, Any], None, None]:
    """
    Mock requests library.

    Args:
        monkeypatch: Pytest's monkeypatch fixture.

    Yields:
        Dictionary containing mock responses.
    """
    mock_responses: dict[str, dict[str, Any]] = {}

    def mock_request(method: str, url: str, **kwargs: Any) -> MockResponse:
        key = f"{method}:{url}"
        if key in mock_responses:
            response_data = mock_responses[key]
            return MockResponse(
                status_code=response_data["status_code"],
                json_data=response_data.get("json_data"),
                text=response_data.get("text"),
            )
        return MockResponse(404)

    monkeypatch.setattr("requests.request", mock_request)
    monkeypatch.setattr(
        "requests.get",
        lambda url, **kwargs: mock_request("GET", url, **kwargs),
    )
    monkeypatch.setattr(
        "requests.post",
        lambda url, **kwargs: mock_request("POST", url, **kwargs),
    )
    monkeypatch.setattr(
        "requests.put",
        lambda url, **kwargs: mock_request("PUT", url, **kwargs),
    )
    monkeypatch.setattr(
        "requests.delete",
        lambda url, **kwargs: mock_request("DELETE", url, **kwargs),
    )

    yield mock_responses
