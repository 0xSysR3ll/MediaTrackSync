"""
This module contains the Jellyfin media manager implementation.
"""

from typing import Any, Dict, Optional

from app.utils.logger import logging as log

from .base import BaseMediaManager


class JellyfinManager(BaseMediaManager):
    """
    Implementation of the Jellyfin media manager.
    """

    def parse_webhook(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Parse webhook data from Jellyfin.

        Args:
            data: The webhook data to parse

        Returns:
            Dict containing parsed media information or None if invalid
        """
        try:
            # Check if this is a scrobble event and if it's completed
            if (
                data.get("event") != "PlaybackStop"
                or data.get("played_to_completion") != "True"
            ):
                return None

            # Get user information
            username = data.get("username")
            if not username:
                log.error("Username not found in Jellyfin webhook")
                return None

            # Get media information
            item_type = data.get("item_type", "").lower()
            if item_type not in ["movie", "episode"]:
                log.error(
                    "Invalid item type in Jellyfin webhook: %s", item_type
                )
                return None

            # Get title based on media type
            if item_type == "episode":
                # For episodes, we need the series name
                series_name = data.get(
                    "series_name"
                )  # This will come from the updated webhook template
                if not series_name:
                    log.error("Series name not found in Jellyfin webhook")
                    return None
                title = series_name
            else:
                title = data.get("title")
                if not title:
                    log.error("Title not found in Jellyfin webhook")
                    return None

            return {
                "type": "movie" if item_type == "movie" else "show",
                "title": title,
                "user_id": username,  # Use username as the user identifier
                "username": username,
                "metadata": data,  # Store all data in metadata for later use
            }

        except Exception as e:
            log.error("Error parsing Jellyfin webhook: %s", e)
            return None

    def extract_media_details(
        self, media_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Extract all media details and identifiers from Jellyfin metadata.

        Args:
            media_info: The media information from parse_webhook

        Returns:
            Dict containing all media details (title, year, season, episode) and identifiers (TVDB, TMDB, IMDB)
        """
        metadata = media_info.get("metadata", {})

        details = {
            "tvdb": metadata.get("tvdb_id"),
            "tmdb": metadata.get("tmdb_id"),
            "imdb": metadata.get("imdb_id"),
            "show_title": None,
            "season": None,
            "episode": None,
            "year": metadata.get("year"),
        }

        # Debug log the metadata
        log.debug("Media type: %s", media_info["type"])
        log.debug("Metadata: %s", metadata)

        # Get show title and year
        if media_info["type"] == "show":
            details["show_title"] = metadata.get(
                "series_name"
            )  # Use series_name for shows
            details["season"] = metadata.get("season_number")
            details["episode"] = metadata.get("episode_number")
            log.debug(
                "Show info - Title: %s, Year: %s, Season: %s, Episode: %s",
                details["show_title"],
                details["year"],
                details["season"],
                details["episode"],
            )
        else:
            details["show_title"] = metadata.get("title")
            log.debug(
                "Movie info - Title: %s, Year: %s",
                details["show_title"],
                details["year"],
            )

        return details
