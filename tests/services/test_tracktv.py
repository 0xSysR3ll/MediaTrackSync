"""
Tests for the TrackTV service.
"""

import pytest

from app.services.tracktv import TrackTVService


def test_tracktv_service_init():
    """Test TrackTV service initialization."""
    service = TrackTVService(
        client_id="test-client-id",
        client_secret="test-client-secret",
        code="test-auth-code",
        redirect_uri="http://127.0.0.1:5000",
    )
    assert service.SERVICE_NAME == "TrackTV"
    assert service.username == "test-client-id"
    assert service.password == "test-client-secret"
    assert service.code == "test-auth-code"
    assert service.redirect_uri == "http://127.0.0.1:5000"


def test_tracktv_service_login_success(mock_requests):
    """Test successful login to TrackTV."""
    mock_requests["POST:https://api.trakt.tv/oauth/token"] = {
        "status_code": 200,
        "json_data": {
            "access_token": "test-access-token",
            "refresh_token": "test-refresh-token",
            "expires_in": 7200,
        },
    }

    service = TrackTVService(
        client_id="test-client-id",
        client_secret="test-client-secret",
        code="test-auth-code",
        redirect_uri="http://127.0.0.1:5000",
    )
    service.login()

    assert service.access_token == "test-access-token"
    assert service.refresh_token == "test-refresh-token"


def test_tracktv_service_login_failure(mock_requests):
    """Test failed login to TrackTV."""
    mock_requests["POST:https://api.trakt.tv/oauth/token"] = {
        "status_code": 401,
        "json_data": {
            "error": "invalid_grant",
            "error_description": "Invalid authorization code",
        },
    }

    service = TrackTVService(
        client_id="test-client-id",
        client_secret="test-client-secret",
        code="invalid-code",
        redirect_uri="http://127.0.0.1:5000",
    )

    with pytest.raises(
        ValueError, match="Invalid Trakt.tv credentials or authorization code"
    ):
        service.login()


def test_tracktv_service_watch_episode_success(mock_requests):
    """Test successful episode watch on TrackTV."""
    # Mock login response
    mock_requests["POST:https://api.trakt.tv/oauth/token"] = {
        "status_code": 200,
        "json_data": {
            "access_token": "test-access-token",
            "refresh_token": "test-refresh-token",
            "expires_in": 7200,
        },
    }

    # Mock watch episode response
    mock_requests["POST:https://api.trakt.tv/sync/history"] = {
        "status_code": 201,
        "json_data": {"added": {"episodes": 1}, "not_found": {"episodes": []}},
    }

    service = TrackTVService(
        client_id="test-client-id",
        client_secret="test-client-secret",
        code="test-auth-code",
        redirect_uri="http://127.0.0.1:5000",
    )

    service.watch_episode(
        episode_id=123,
        show_title="Test Show (2020)",
        season=1,
        episode=1,
        year=2020,
        imdb_id="tt1234567",
    )

    # Verify the request was made with correct data
    request = mock_requests["POST:https://api.trakt.tv/sync/history"]
    assert request["status_code"] == 201


def test_tracktv_service_watch_episode_missing_info(mock_requests):
    """Test episode watch with missing information."""
    service = TrackTVService(
        client_id="test-client-id",
        client_secret="test-client-secret",
        code="test-auth-code",
        redirect_uri="http://127.0.0.1:5000",
    )

    # Test with missing show title
    service.watch_episode(
        episode_id=123, season=1, episode=1, year=2020, imdb_id="tt1234567"
    )

    # Verify no request was made
    assert "POST:https://api.trakt.tv/sync/history" not in mock_requests


def test_tracktv_service_watch_movie_success(mock_requests):
    """Test successful movie watch on TrackTV."""
    # Mock login response
    mock_requests["POST:https://api.trakt.tv/oauth/token"] = {
        "status_code": 200,
        "json_data": {
            "access_token": "test-access-token",
            "refresh_token": "test-refresh-token",
            "expires_in": 7200,
        },
    }

    # Mock watch movie response
    mock_requests["POST:https://api.trakt.tv/sync/history"] = {
        "status_code": 201,
        "json_data": {"added": {"movies": 1}, "not_found": {"movies": []}},
    }

    service = TrackTVService(
        client_id="test-client-id",
        client_secret="test-client-secret",
        code="test-auth-code",
        redirect_uri="http://127.0.0.1:5000",
    )

    mock_requests["POST:https://api.trakt.tv/oauth/token"] = {
        "status_code": 200,
        "json_data": {
            "access_token": "test-access-token",
            "refresh_token": "test-refresh-token",
            "expires_in": 7200,
        },
    }

    service.watch_movie(
        tmdb_id=456, imdb_id="tt1234567", movie_title="Test Movie"
    )

    # Verify the request was made with correct data
    request = mock_requests["POST:https://api.trakt.tv/sync/history"]
    assert request["status_code"] == 201


def test_tracktv_service_watch_movie_missing_info(mock_requests):
    """Test movie watch with missing information."""
    mock_requests["POST:https://api.trakt.tv/oauth/token"] = {
        "status_code": 200,
        "json_data": {
            "access_token": "test-access-token",
            "refresh_token": "test-refresh-token",
            "expires_in": 7200,
        },
    }

    service = TrackTVService(
        client_id="test-client-id",
        client_secret="test-client-secret",
        code="test-auth-code",
        redirect_uri="http://127.0.0.1:5000",
    )

    service.watch_movie(tmdb_id=456)  # not enough info to proceed

    assert "POST:https://api.trakt.tv/sync/history" not in mock_requests
