"""
This module contains the Plex media manager implementation.
"""

from typing import Any, Dict, Optional

from app.utils.logger import logging as log

from .base import BaseMediaManager


class PlexManager(BaseMediaManager):
    """
    Implementation of the Plex media manager.
    """

    def parse_webhook(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Parse webhook data from Plex.

        Args:
            data: The webhook data to parse

        Returns:
            Dict containing parsed media information or None if invalid
        """
        try:
            # Debug log the incoming data
            log.debug("Received webhook data: %s", data)

            # Check if this is a scrobble event
            if data.get("event") != "media.scrobble":
                return None

            metadata = data.get("Metadata")
            if not metadata:
                log.error("Metadata not found in Plex webhook")
                return None

            # Get user information
            account = data.get("Account", {})
            user_id = account.get("title", "").lower()
            if not user_id:
                log.error("User ID not found in Plex webhook")
                return None

            # Get media information
            media_type = metadata.get("librarySectionType")
            if media_type not in ["movie", "show"]:
                log.error("Invalid media type in Plex webhook: %s", media_type)
                return None

            if media_type == "movie":
                title = metadata.get("title")
            else:
                title = metadata.get("grandparentTitle")

            if not title:
                log.error("Title not found in Plex webhook")
                return None

            # Debug log the parsed information
            log.debug(
                "Parsed webhook - Type: %s, Title: %s, User: %s",
                media_type,
                title,
                user_id,
            )
            log.debug("Full metadata: %s", metadata)

            return {
                "type": media_type,
                "title": title,
                "user_id": user_id,
                "metadata": metadata,
            }

        except Exception as e:
            log.error("Error parsing Plex webhook: %s", e)
            return None

    def get_user_info(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a user.
        Since Plex webhooks provide the user ID directly, we just return it.

        Args:
            user_id: The ID of the user from Plex

        Returns:
            Dict containing user information
        """
        # Plex webhooks provide the user ID directly, so we just return it
        return {"id": user_id}

    def extract_media_details(
        self, media_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Extract all media details and identifiers from Plex metadata.

        Args:
            media_info: The media information from parse_webhook

        Returns:
            Dict containing all media details (title, year, season, episode) and identifiers (TVDB, TMDB, IMDB)
        """
        metadata = media_info.get("metadata", {})
        guids = metadata.get("Guid", [])

        details = {
            "tvdb": None,
            "tmdb": None,
            "imdb": None,
            "show_title": None,
            "season": None,
            "episode": None,
            "year": None,
        }

        # Debug log the metadata
        log.debug("Media type: %s", media_info["type"])
        log.debug("Metadata: %s", metadata)

        # Get show title and year
        if media_info["type"] == "show":
            details["show_title"] = metadata.get("grandparentTitle")
            details["year"] = metadata.get(
                "year"
            )  # Use the year field directly
            details["season"] = metadata.get("parentIndex")  # Season number
            details["episode"] = metadata.get("index")  # Episode number
            log.debug(
                "Show info - Title: %s, Year: %s, Season: %s, Episode: %s",
                details["show_title"],
                details["year"],
                details["season"],
                details["episode"],
            )
        else:
            details["show_title"] = metadata.get("title")
            details["year"] = metadata.get("year")
            log.debug(
                "Movie info - Title: %s, Year: %s",
                details["show_title"],
                details["year"],
            )

        for guid in guids:
            guid_id = guid.get("id", "")
            if guid_id.startswith("tvdb://"):
                try:
                    details["tvdb"] = guid_id.split("tvdb://")[-1]
                except Exception as e:
                    log.error("Error extracting TVDB ID: %s", e)
            elif guid_id.startswith("tmdb://"):
                try:
                    details["tmdb"] = guid_id.split("tmdb://")[-1]
                except Exception as e:
                    log.error("Error extracting TMDB ID: %s", e)
            elif guid_id.startswith("imdb://"):
                try:
                    details["imdb"] = guid_id.split("imdb://")[-1]
                except Exception as e:
                    log.error("Error extracting IMDB ID: %s", e)

        return details
