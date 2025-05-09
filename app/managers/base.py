"""
This module contains the base class for media managers.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


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
    def get_media_info(self, media_id: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a media item.

        Args:
            media_id: The ID of the media item

        Returns:
            Dict containing media information or None if not found
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
    def get_media_ids(self, media_info: Dict[str, Any]) -> List[str]:
        """
        Get all possible IDs for a media item (e.g., TVDB, TMDB, etc.).

        Args:
            media_info: The media information

        Returns:
            List of media IDs
        """
        pass
