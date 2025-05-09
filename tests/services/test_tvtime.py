from unittest.mock import MagicMock, patch

import pytest

from app.services.tvtime import TVTimeService


@pytest.fixture
def tvtime_service():
    return TVTimeService("test_user", "test_pass")


def test_watch_episode(tvtime_service):
    with patch("app.services.tvtime.requests.post") as mock_post:
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "result": "OK",
            "season": {"number": 1},
            "number": 1,
            "show": {"name": "Test Show"},
        }
        mock_post.return_value = mock_response

        tvtime_service.token = "test_token"
        tvtime_service.watch_episode(
            episode_id=123,
            show_title="Test Show",
            season=1,
            episode=1,
            tmdb_id=456,
            imdb_id="tt123456",
        )

        mock_post.assert_called_once()


def test_watch_movie(tvtime_service):
    with (
        patch("app.services.tvtime.requests.post") as mock_post,
        patch.object(
            tvtime_service, "get_movie_uuid", return_value="test-uuid-123"
        ),
    ):
        mock_response = MagicMock()
        mock_response.json.return_value = {"status": "success"}
        mock_post.return_value = mock_response

        tvtime_service.token = "test_token"
        tvtime_service.watch_movie(
            movie_id=123, tmdb_id=456, imdb_id="tt123456"
        )

        mock_post.assert_called_once()
