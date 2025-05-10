"""
This module contains the TVTime service implementation.
"""

import json
import os
import sys
import time
from typing import Any, Dict, Optional

import requests
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service

from app.utils.logger import logging as log

from .base import BaseService

BASE_URL = "app.tvtime.com"


class TVTimeService(BaseService):
    """
    Implementation of the TVTime tracking service using Selenium.
    """

    SERVICE_NAME = "TVTime"

    def __init__(self, username: str, password: str):
        """
        Initialize the TVTime service.

        Args:
            username: The TVTime username/email
            password: The TVTime password
        """
        super().__init__(username, password)
        self.token: Optional[str] = None
        self.refresh_token: Optional[str] = None
        self.driver: Optional[webdriver.Firefox] = None
        self.user = username  # Use username as plex_user for logging
        self.last_movie_title: Optional[str] = None

    def _init_driver(self) -> None:
        """
        Initialize the Firefox WebDriver.
        """
        options = Options()
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--allow-origins=*")
        options.binary_location = "/usr/bin/firefox-esr"

        # Try both possible GeckoDriver paths
        geckodriver_paths = [
            "/usr/bin/geckodriver",
            "/usr/local/bin/geckodriver",
        ]
        driver_path = None

        for path in geckodriver_paths:
            if os.path.exists(path) and os.access(path, os.X_OK):
                driver_path = path
                break

        if not driver_path:
            log.error(
                "[%s] GeckoDriver not found in /usr/bin or /usr/local/bin",
                self.SERVICE_NAME,
            )
            sys.exit(1)

        try:
            log.info(
                "[%s] Initializing Firefox driver with GeckoDriver at %s...",
                self.SERVICE_NAME,
                driver_path,
            )
            self.driver = webdriver.Firefox(
                service=Service(driver_path), options=options
            )
        except Exception as e:
            log.error(
                "[%s] Error initializing Firefox driver: %s",
                self.SERVICE_NAME,
                e,
            )
            sys.exit(1)

    def login(self) -> None:
        """
        Log in to TVTime using Selenium.
        """
        if not self.driver:
            self._init_driver()

        if self.driver is None:
            log.error("[%s] Failed to initialize driver", self.SERVICE_NAME)
            sys.exit(1)

        try:
            self.driver.get(f"https://{BASE_URL}/welcome?mode=auth")
            time.sleep(5)  # The page can take a while to load

            jwt_token = None
            for i in range(1, 4):
                time.sleep(5 + (2 * i))  # Wait a bit longer each time
                log.debug(
                    "[%s] Attempt %d to fetch JWT token", self.SERVICE_NAME, i
                )
                try:
                    jwt_token = self.driver.execute_script(
                        "return window.localStorage.getItem('flutter.jwtToken');"
                    )
                    if jwt_token:
                        break
                except Exception as e:
                    log.error(
                        "[%s] Error fetching JWT token: %s",
                        self.SERVICE_NAME,
                        e,
                    )
                    break

            if jwt_token is None:
                log.error(
                    "[%s] Unable to fetch JWT token using Selenium",
                    self.SERVICE_NAME,
                )
                self.driver.quit()
                sys.exit(1)

            log.info(
                "[%s] JWT token fetched successfully! Exiting Selenium...",
                self.SERVICE_NAME,
            )
            self.driver.quit()
            self.driver = None

            jwt_token = jwt_token.strip('"')
            headers = {
                "Authorization": f"Bearer {jwt_token}",
                "Content-Type": "application/json",
            }
            credentials = {
                "username": self.username,
                "password": self.password,
            }

            log.debug(
                "[%s] Trying to connect to %s's TVTime account...",
                self.SERVICE_NAME,
                self.user,
            )
            login_url = (
                "https://beta-app.tvtime.com/sidecar?"
                "o=https://auth.tvtime.com/v1/login"
            )

            try:
                response = requests.post(
                    url=login_url,
                    headers=headers,
                    data=json.dumps(credentials),
                    timeout=(5, 10),
                )

                # Handle 400 errors specifically
                if response.status_code == 400:
                    try:
                        error_data = response.json()
                        error_msg = error_data.get(
                            "message", "Invalid credentials"
                        )
                        log.error(
                            "[%s] Login failed: %s",
                            self.SERVICE_NAME,
                            error_msg,
                        )
                        raise ValueError(
                            f"Invalid TVTime credentials: {error_msg}"
                        )
                    except json.JSONDecodeError as e:
                        log.error(
                            "[%s] Login failed: Invalid credentials format",
                            self.SERVICE_NAME,
                        )
                        raise ValueError(
                            "Invalid TVTime credentials format"
                        ) from e

                # Handle 401 errors specifically
                if response.status_code == 401:
                    log.error(
                        "[%s] Login failed: Invalid TVTime credentials (username or password)",
                        self.SERVICE_NAME,
                    )
                    raise ValueError(
                        "Invalid TVTime credentials - please check your username and password"
                    )

                response.raise_for_status()

            except requests.exceptions.RequestException as e:
                if isinstance(e, requests.exceptions.HTTPError):
                    if e.response.status_code == 401:
                        log.error(
                            "[%s] Login failed: Invalid TVTime credentials (username or password)",
                            self.SERVICE_NAME,
                        )
                        raise ValueError(
                            "Invalid TVTime credentials - please check your username and password"
                        ) from e
                    log.error(
                        "[%s] HTTP error during login: %s",
                        self.SERVICE_NAME,
                        e,
                    )
                else:
                    log.error(
                        "[%s] Error connecting to TVTime API: %s",
                        self.SERVICE_NAME,
                        e,
                    )
                raise

            try:
                auth_resp = response.json()
            except json.JSONDecodeError as e:
                log.error(
                    "[%s] Error decoding JSON response: %s",
                    self.SERVICE_NAME,
                    e,
                )
                sys.exit(1)

            if auth_resp is None:
                log.error(
                    "[%s] Error fetching JWT tokens from TVTime API",
                    self.SERVICE_NAME,
                )
                sys.exit(1)

            try:
                self.token = auth_resp["data"]["jwt_token"]
                self.refresh_token = auth_resp["data"]["jwt_refresh_token"]
            except KeyError as e:
                log.error(
                    "[%s] Error crafting JWT token for TVTime API: %s",
                    self.SERVICE_NAME,
                    e,
                )
                sys.exit(1)

            log.info(
                "[%s] Successfully connected to %s's TVTime account!",
                self.SERVICE_NAME,
                self.user,
            )

        except Exception as e:
            log.error(
                "[%s] Error logging in to TVTime: %s", self.SERVICE_NAME, e
            )
            raise

    def _get_headers(self) -> Dict[str, str]:
        """
        Get the headers for API requests.

        Returns:
            Dict containing the headers
        """
        if not self.token:
            self.login()
        return {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
            "Host": f"{BASE_URL}:80",
        }

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
            show_title: The title of the show (optional)
            season: The season number (optional)
            episode: The episode number (optional)
            year: The year the show started (optional)
            tmdb_id: The TMDB ID of the episode (optional)
            imdb_id: The IMDB ID of the episode (optional)
        """
        if not self.token:
            self.login()

        try:
            watch_api = (
                f"https://{BASE_URL}/sidecar?"
                f"o=https://api2.tozelabs.com/v2/watched_episodes/episode/{episode_id}"
                "&is_rewatch=0"
            )
            response = requests.post(
                url=watch_api,
                headers=self._get_headers(),
                data=json.dumps(self.refresh_token),
                timeout=(5, 10),
            )
            response.raise_for_status()

            result = response.json()
            status = result.get("result")
            if status is None or status != "OK":
                log.error(
                    "[%s] Error while watching episode!", self.SERVICE_NAME
                )
                return

            season = result.get("season", {}).get("number")
            episode = result.get("number")
            show = result.get("show", {}).get("name")

            log.info(
                "[%s] Successfully marked %s S%sE%s as watched!",
                self.SERVICE_NAME,
                show,
                season,
                episode,
            )

        except Exception as e:
            log.error(
                "[%s] Error marking episode as watched: %s",
                self.SERVICE_NAME,
                e,
            )
            raise

    def watch_movie(
        self,
        movie_id: int,
        tmdb_id: Optional[int] = None,
        imdb_id: Optional[str] = None,
        movie_title: Optional[str] = None,
    ) -> None:
        """
        Mark a movie as watched.

        Args:
            movie_id: The TVDB ID of the movie to mark as watched
            tmdb_id: The TMDB ID of the movie (optional)
            imdb_id: The IMDB ID of the movie (optional)
            movie_title: The title of the movie (optional)
        """
        if not self.token:
            self.login()

        if not (imdb_id or tmdb_id):
            log.warning("[%s] Skipping movie, no valid ID", self.SERVICE_NAME)
            return

        # Store the movie title for potential title-based search
        if movie_title:
            self.last_movie_title = movie_title

        try:
            movie_uuid = self.get_movie_uuid(
                movie_id=movie_id, tmdb_id=tmdb_id, imdb_id=imdb_id
            )
            if movie_uuid is None:
                log.error(
                    "[%s] Could not find movie UUID for ID: %s (TMDB: %s, IMDB: %s)",
                    self.SERVICE_NAME,
                    movie_id,
                    tmdb_id,
                    imdb_id,
                )
                return

            watch_api = (
                f"https://{BASE_URL}/sidecar?"
                f"o=https://msapi.tvtime.com/prod/v1/tracking/{movie_uuid}/watch"
            )
            response = requests.post(
                url=watch_api, headers=self._get_headers(), timeout=(5, 10)
            )
            response.raise_for_status()

            result = response.json()
            status = result.get("status")
            if status is None or status != "success":
                log.error(
                    "[%s] Error while watching movie!", self.SERVICE_NAME
                )
                return

            # Use movie title in log if available
            if movie_title:
                log.info(
                    "[%s] Successfully marked '%s' as watched!",
                    self.SERVICE_NAME,
                    movie_title,
                )
            else:
                log.info(
                    "[%s] Successfully marked movie (ID: %s) as watched!",
                    self.SERVICE_NAME,
                    movie_id,
                )

        except Exception as e:
            log.error(
                "[%s] Error marking movie as watched: %s", self.SERVICE_NAME, e
            )
            raise

    def get_movie_uuid(
        self,
        movie_id: int,
        tmdb_id: Optional[int] = None,
        imdb_id: Optional[str] = None,
    ) -> Optional[str]:
        """
        Get the UUID of a movie from TVTime.

        Args:
            movie_id: The TVDB ID of the movie
            tmdb_id: The TMDB ID of the movie (optional)
            imdb_id: The IMDB ID of the movie (optional)

        Returns:
            The movie UUID if found, None otherwise
        """
        if not self.token:
            self.login()

        # Try different search methods in order of preference
        search_methods = [
            # Try TVDB ID first
            lambda: self._search_by_id(movie_id),
            # Try TMDB ID if available
            lambda: self._search_by_id(tmdb_id) if tmdb_id else None,
            # Try IMDB ID if available
            lambda: self._search_by_id(imdb_id) if imdb_id else None,
            # Try title search as last resort
            lambda: (
                self._search_by_title()
                if hasattr(self, "last_movie_title") and self.last_movie_title
                else None
            ),
        ]

        for search_method in search_methods:
            try:
                uuid = search_method()
                if uuid:
                    return uuid
            except Exception as e:
                log.debug(
                    "[%s] Search method failed: %s", self.SERVICE_NAME, e
                )
                continue

        log.warning(
            "[%s] Movie not found in TVTime database (TVDB: %s, TMDB: %s, IMDB: %s)",
            self.SERVICE_NAME,
            movie_id,
            tmdb_id,
            imdb_id,
        )
        return None

    def _search_by_id(self, id_value: Any) -> Optional[str]:
        """
        Search for a movie by ID.

        Args:
            id_value: The ID to search for (TVDB, TMDB, or IMDB)

        Returns:
            The movie UUID if found, None otherwise
        """
        search_url = (
            f"https://{BASE_URL}/sidecar?"
            f"o=https://search.tvtime.com/v1/search/series,movie&q={id_value}"
            "&offset=0&limit=1"
        )
        response = requests.get(
            url=search_url, headers=self._get_headers(), timeout=(5, 10)
        )
        response.raise_for_status()

        search = response.json()
        if search.get("status") != "success":
            return None

        movies = search.get("data", [])
        for movie in movies:
            if movie.get("type") == "movie":  # Ensure we only get movies
                return movie.get("uuid")

        return None

    def _search_by_title(self) -> Optional[str]:
        """
        Search for a movie by title.

        Returns:
            The movie UUID if found, None otherwise
        """
        search_url = (
            f"https://{BASE_URL}/sidecar?"
            f"o=https://search.tvtime.com/v1/search/series,movie&q={self.last_movie_title}"
            "&offset=0&limit=5"  # Increased limit to improve chances of finding the movie
        )
        response = requests.get(
            url=search_url, headers=self._get_headers(), timeout=(5, 10)
        )
        response.raise_for_status()

        search = response.json()
        if search.get("status") != "success":
            return None

        movies = search.get("data", [])
        for movie in movies:
            if movie.get("type") == "movie":  # Ensure we only get movies
                return movie.get("uuid")

        return None
