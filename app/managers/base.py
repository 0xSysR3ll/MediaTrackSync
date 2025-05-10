"""
This module contains the base class for media managers.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional


class BaseMediaManager(ABC):
    """
    Base class for all media managers.
    """

    @abstractmethod
    def parse_webhook(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Parse webhook data from the media manager.

        Args:
            data: The webhook data to parse

        Returns:
            Dict containing parsed media information or None if invalid
        """
        pass

    @abstractmethod
    def get_user_info(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a user.

        Args:
            user_id: The ID of the user

        Returns:
            Dict containing user information or None if not found
        """
        pass

    @abstractmethod
    def extract_media_details(
        self, media_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Extract all media details and identifiers from the parsed webhook data.

        Args:
            media_info: The media information from parse_webhook

        Returns:
            Dict containing all media details (title, year, season, episode) and identifiers (TVDB, TMDB, IMDB)
        """
        pass
