"""
This module provides the base interface for tracking services.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Protocol


class TrackingService(Protocol):
    """
    Protocol defining the interface for tracking services.
    """

    @property
    def SERVICE_NAME(self) -> str:
        """
        Get the name of the service.

        Returns:
            The service name.
        """
        ...

    def login(self) -> None:
        """
        Log in to the tracking service.
        """
        ...

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
            episode_id: The TVDB ID of the episode to mark as watched.
            show_title: The title of the show.
            season: The season number.
            episode: The episode number.
            year: The year the show started.
            tmdb_id: The TMDB ID of the episode.
            imdb_id: The IMDB ID of the episode.
        """
        ...

    def watch_movie(
        self,
        movie_id: int,
        tmdb_id: Optional[int] = None,
        imdb_id: Optional[str] = None,
    ) -> None:
        """
        Mark a movie as watched.

        Args:
            movie_id: The TVDB ID of the movie to mark as watched.
            tmdb_id: The TMDB ID of the movie.
            imdb_id: The IMDB ID of the movie.
        """
        ...

    def get_episode_info(self, episode_id: int) -> Optional[Dict[str, Any]]:
        """
        Get information about an episode.

        Args:
            episode_id: The TVDB ID of the episode.

        Returns:
            Dictionary containing episode information or None if not found.
        """
        ...

    def get_movie_info(self, movie_id: int) -> Optional[Dict[str, Any]]:
        """
        Get information about a movie.

        Args:
            movie_id: The TVDB ID of the movie.

        Returns:
            Dictionary containing movie information or None if not found.
        """
        ...


class BaseService(ABC):
    """Base class for all tracking services."""

    SERVICE_NAME: str = "Base"

    def __init__(self, username: str, password: str):
        """
        Initialize the base service.

        Args:
            username: The service username/email
            password: The service password
        """
        self.username = username
        self.password = password
        self.token: Optional[str] = None

    @abstractmethod
    def login(self) -> None:
        """Log in to the service."""
        pass

    @abstractmethod
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
        pass

    @abstractmethod
    def watch_movie(
        self,
        movie_id: int,
        tmdb_id: Optional[int] = None,
        imdb_id: Optional[str] = None,
    ) -> None:
        """
        Mark a movie as watched.

        Args:
            movie_id: The TVDB ID of the movie to mark as watched
            tmdb_id: The TMDB ID of the movie (optional)
            imdb_id: The IMDB ID of the movie (optional)
        """
        pass

    @abstractmethod
    def get_episode_info(self, episode_id: int) -> Optional[Dict[str, Any]]:
        """
        Get information about an episode.

        Args:
            episode_id: The TVDB ID of the episode.

        Returns:
            Dictionary containing episode information or None if not found.
        """
        pass

    @abstractmethod
    def get_movie_info(self, movie_id: int) -> Optional[Dict[str, Any]]:
        """
        Get information about a movie.

        Args:
            movie_id: The TVDB ID of the movie.

        Returns:
            Dictionary containing movie information or None if not found.
        """
        pass
