"""
This module contains the TrackTV (Trakt.tv) service implementation.
"""

import json
import time
from typing import Any, Dict, Optional

import requests

from app.utils.logger import logging as log

from .base import BaseService


class TrackTVService(BaseService):
    """
    Implementation of the TrackTV (Trakt.tv) tracking service.
    """

    BASE_URL = "https://api.trakt.tv"
    TOKEN_URL = f"{BASE_URL}/oauth/token"
    HISTORY_URL = f"{BASE_URL}/sync/history"
    SERVICE_NAME = "TrackTV"

    def __init__(
        self, client_id: str, client_secret: str, code: str, redirect_uri: str
    ):
        """
        Initialize the TrackTV service.

        Args:
            client_id: The Trakt.tv client ID
            client_secret: The Trakt.tv client secret
            code: The authorization code from OAuth flow
            redirect_uri: The redirect URI used in OAuth flow
        """
        super().__init__(
            client_id, client_secret
        )  # Store credentials in base class
        self.client_id = client_id  # Store client_id for OAuth flow
        self.client_secret = (
            client_secret  # Store client_secret for OAuth flow
        )
        self.code = code
        self.redirect_uri = redirect_uri
        self.access_token = None
        self.refresh_token = None
        self.token_expires_at = 0

    def _get_headers(self) -> Dict[str, str]:
        """
        Get the headers for API requests.

        Returns:
            Dict containing the headers
        """
        if not self.access_token or time.time() >= self.token_expires_at:
            self.login()

        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.access_token}",
            "trakt-api-version": "2",
            "trakt-api-key": (
                self.client_id
            ),  # Use client_id instead of username
        }

    def login(self) -> None:
        """
        Log in to Trakt.tv using OAuth2.

        Raises:
            ValueError: If login fails.
        """
        try:
            response = requests.post(
                "https://api.trakt.tv/oauth/token",
                json={
                    "code": self.code,
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "redirect_uri": self.redirect_uri,
                    "grant_type": "authorization_code",
                },
                headers={"Content-Type": "application/json"},
            )
            response.raise_for_status()
            data = response.json()
            self.access_token = data["access_token"]
            self.refresh_token = data["refresh_token"]
            self.token_expires_at = time.time() + data.get(
                "expires_in", 7200
            )  # Default to 2 hours
            log.info(
                f"[{self.SERVICE_NAME}] Successfully logged in to Trakt.tv"
            )
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 400:
                log.error(
                    f"[{self.SERVICE_NAME}] Authorization code expired or invalid. "
                    "Please generate a new authorization code by visiting: "
                    f"https://trakt.tv/oauth/authorize?response_type=code&client_id={self.client_id}&redirect_uri={self.redirect_uri}"
                )
            else:
                log.error(
                    f"[{self.SERVICE_NAME}] Error logging in to Trakt.tv: {e}"
                )
            raise ValueError(
                "Invalid Trakt.tv credentials or authorization code"
            ) from e
        except Exception as e:
            log.error(
                f"[{self.SERVICE_NAME}] Error logging in to Trakt.tv: {e}"
            )
            raise ValueError(
                "Invalid Trakt.tv credentials or authorization code"
            ) from e

    def _handle_rate_limit(self, response: requests.Response) -> None:
        """
        Handle rate limit response from Trakt.tv API.

        Args:
            response: The response from the API
        """
        # Get rate limit info from headers
        rate_limit = response.headers.get("x-ratelimit")
        retry_after = response.headers.get(
            "retry-after", "1"
        )  # Default to 1 second if not provided

        if rate_limit:
            try:
                rate_data = json.loads(rate_limit)
                log.warning(
                    "[%s] Rate limit reached. %s. Retrying in %s seconds.",
                    self.SERVICE_NAME,
                    rate_data.get("name", "Unknown limit"),
                    retry_after,
                )
                time.sleep(int(retry_after))
            except json.JSONDecodeError:
                log.warning(
                    "[%s] Could not parse rate limit header", self.SERVICE_NAME
                )
                time.sleep(int(retry_after))

    def _make_trakt_request(
        self,
        data: Dict[str, Any],
        show_title: str,
        season: Optional[int] = None,
        episode: Optional[int] = None,
    ) -> bool:
        """
        Make a request to Trakt.tv API with retry logic.

        Args:
            data: The data to send to Trakt.tv
            show_title: The title of the show (for logging)
            season: The season number (for logging)
            episode: The episode number (for logging)

        Returns:
            bool: True if the request was successful, False otherwise
        """
        max_retries = 3
        retry_count = 0

        while retry_count < max_retries:
            response = requests.post(
                url=self.HISTORY_URL,
                headers=self._get_headers(),
                data=json.dumps(data),
                timeout=(5, 10),
            )

            # Handle rate limiting
            if response.status_code == 429:
                self._handle_rate_limit(response)
                retry_count += 1
                continue

            if response.status_code == 409:
                log.info(
                    "[%s] Episode was already marked as watched recently",
                    self.SERVICE_NAME,
                )
                return True

            response.raise_for_status()
            response_data = response.json()
            log.debug("Response: %s", response_data)

            # Check for not_found items
            not_found = response_data.get("not_found", {})
            if not_found.get("episodes"):
                log.error(
                    "[%s] Episode S%sE%s of %s not found in Trakt.tv database",
                    self.SERVICE_NAME,
                    season,
                    episode,
                    show_title,
                )
                return False
            if not_found.get("shows"):
                log.error(
                    "[%s] Show not found in Trakt.tv database: %s",
                    self.SERVICE_NAME,
                    show_title,
                )
                return False
            if not_found.get("seasons"):
                log.error(
                    "[%s] Season %s of %s not found in Trakt.tv database",
                    self.SERVICE_NAME,
                    season,
                    show_title,
                )
                return False

            # Log success
            log.info(
                "[%s] Successfully marked %s S%sE%s as watched!",
                self.SERVICE_NAME,
                show_title,
                season,
                episode,
            )
            return True

        raise Exception("Max retries exceeded for rate limit")

    def watch_episode(
        self,
        episode_id: int,
        show_title: Optional[str] = None,
        season: Optional[int] = None,
        episode: Optional[int] = None,
        year: Optional[int] = None,
        tmdb_id: Optional[int] = None,
        imdb_id: Optional[str] = None,
    ) -> None:
        """
        Mark an episode as watched.

        Args:
            episode_id: The TVDB ID of the episode to mark as watched
            show_title: The title of the show
            season: The season number
            episode: The episode number
            year: The year the show started
            tmdb_id: The TMDB ID of the episode
            imdb_id: The IMDB ID of the episode or show
        """
        try:
            if not all([show_title, season, episode]):
                log.error(
                    "[%s] Missing required show information (title, season, episode)",
                    self.SERVICE_NAME,
                )
                return

            # If we have an IMDB ID, try the direct episode method first
            if imdb_id:
                data = {
                    "episodes": [
                        {
                            "ids": {
                                "imdb": imdb_id,
                            },
                            "watched_at": time.strftime(
                                "%Y-%m-%dT%H:%M:%S.000Z",
                                time.gmtime(),
                            ),
                        }
                    ]
                }

                log.debug("Trying direct episode method with data: %s", data)
                if self._make_trakt_request(data, show_title, season, episode):
                    return

            # Extract the year from the show title (e.g., "S.W.A.T. (2017)" -> 2017)
            show_year = None
            if show_title and "(" in show_title and ")" in show_title:
                try:
                    year_str = show_title.split("(")[-1].split(")")[0]
                    show_year = int(year_str)
                except (ValueError, IndexError):
                    pass

            # Use provided year if available, otherwise use extracted year
            show_year = year if year is not None else show_year

            # Try the show method
            data = {
                "shows": [
                    {
                        "title": (
                            show_title.split(" (")[0]
                            if show_year
                            else show_title
                        ),  # Remove year from title
                        "year": show_year,  # Use the year
                        "ids": {
                            "imdb": imdb_id,  # Use IMDB ID for the show
                        },
                        "seasons": [
                            {
                                "number": season,
                                "episodes": [
                                    {
                                        "number": episode,
                                        "watched_at": time.strftime(
                                            "%Y-%m-%dT%H:%M:%S.000Z",
                                            time.gmtime(),
                                        ),
                                    }
                                ],
                            }
                        ],
                    }
                ]
            }

            log.debug("Trying show method with data: %s", data)
            self._make_trakt_request(data, show_title, season, episode)

        except Exception as e:
            log.error(
                "[%s] Error marking episode as watched: %s",
                self.SERVICE_NAME,
                e,
            )
            raise

    def _watch_episode_direct(
        self,
        imdb_id: str,
        show_title: str,
        season: int,
        episode: int,
    ) -> None:
        """
        Mark an episode as watched using direct episode ID.
        This is used when we have an episode-specific IMDB ID (e.g., from Jellyfin).

        Args:
            imdb_id: The IMDB ID of the episode
            show_title: The title of the show (for logging)
            season: The season number (for logging)
            episode: The episode number (for logging)
        """
        try:
            data = {
                "episodes": [
                    {
                        "ids": {
                            "imdb": imdb_id,
                        },
                        "watched_at": time.strftime(
                            "%Y-%m-%dT%H:%M:%S.000Z",
                            time.gmtime(),
                        ),
                    }
                ]
            }

            log.debug("Response from traktv API: %s", data)

            max_retries = 3
            retry_count = 0

            while retry_count < max_retries:
                response = requests.post(
                    url=self.HISTORY_URL,
                    headers=self._get_headers(),
                    data=json.dumps(data),
                    timeout=(5, 10),
                )

                # Handle rate limiting
                if response.status_code == 429:
                    self._handle_rate_limit(response)
                    retry_count += 1
                    continue

                if response.status_code == 409:
                    log.info(
                        "[%s] Episode was already marked as watched recently",
                        self.SERVICE_NAME,
                    )
                    return

                response.raise_for_status()
                response_data = response.json()
                log.debug("Response: %s", response_data)

                # Check if the episode was found
                if response_data.get("not_found", {}).get("episodes"):
                    log.error(
                        "[%s] Episode S%sE%s of %s not found in Trakt.tv database",
                        self.SERVICE_NAME,
                        season,
                        episode,
                        show_title,
                    )
                    return

                # Log success with the provided show information
                log.info(
                    "[%s] Successfully marked %s S%sE%s as watched!",
                    self.SERVICE_NAME,
                    show_title,
                    season,
                    episode,
                )
                break

            if retry_count >= max_retries:
                raise Exception("Max retries exceeded for rate limit")

        except Exception as e:
            log.error(
                "[%s] Error marking episode as watched: %s",
                self.SERVICE_NAME,
                e,
            )
            raise

    def watch_movie(
        self,
        tmdb_id: int,
        imdb_id: Optional[str] = None,
        movie_title: Optional[str] = None,
    ) -> None:
        """
        Mark a movie as watched.

        Args:
            tmdb_id: The TMDB ID of the movie to mark as watched
            imdb_id: The IMDB ID of the movie (optional)
            movie_title: The title of the movie (optional)
        """

        if not movie_title or not (tmdb_id or imdb_id):
            log.warning(
                "[%s] Skipping movie watch: missing title or ID",
                self.SERVICE_NAME,
            )
            return

        if not self.access_token:
            self.login()

        data = {
            "movies": [
                {
                    "ids": {
                        "tmdb": tmdb_id,
                    }
                }
            ]
        }

        if imdb_id:
            data["movies"][0]["ids"]["imdb"] = imdb_id

        response = requests.post(
            self.HISTORY_URL,
            headers=self._get_headers(),
            json=data,
            timeout=(5, 10),
        )
        response.raise_for_status()

        # Use the movie title if available, otherwise use a generic message
        if movie_title:
            log.info(
                "[%s] Successfully marked '%s' as watched",
                self.SERVICE_NAME,
                movie_title,
            )
        else:
            log.info(
                "[%s] Successfully marked movie (TMDB ID: %s) as watched",
                self.SERVICE_NAME,
                tmdb_id,
            )
