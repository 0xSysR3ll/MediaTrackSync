"""
This module contains the route handlers for the application.
"""

import json
from typing import Any, Dict, Optional, Tuple

from flask import Flask, Response, make_response, request
from werkzeug.http import parse_options_header

from .services.tracktv import TrackTVService
from .utils.logger import logging as log


def parse_webhook_data() -> Tuple[Optional[str], Optional[Dict[str, Any]]]:
    """
    Parse webhook data from the request.
    Handles JSON, form-encoded, and multipart form data.

    Returns:
        Tuple containing the media manager type and parsed data
    """
    try:
        content_type, pdict = parse_options_header(
            request.headers.get("Content-Type", "")
        )
        if not isinstance(content_type, str):
            log.error("Invalid content type")
            return None, None

        # Handle JSON data
        if content_type == "application/json":
            payload = request.get_json()
            if payload is None:
                # Try to parse raw data as JSON
                try:
                    payload = json.loads(request.get_data(as_text=True))
                except json.JSONDecodeError:
                    log.error("Invalid JSON data")
                    return None, None
            return "jellyfin", payload

        # Handle form-encoded data (application/x-www-form-urlencoded)
        if content_type == "application/x-www-form-urlencoded":
            form_data = request.form.to_dict()
            if not form_data:
                log.error("Empty form data")
                return None, None

            # Try to parse the data as JSON if it's in a single field
            for key, value in form_data.items():
                try:
                    payload = json.loads(value)
                    return "jellyfin", payload
                except json.JSONDecodeError:
                    continue

            # If no JSON field found, use the form data as is
            return "jellyfin", form_data

        # Handle multipart form data
        if content_type.startswith("multipart/form-data"):
            if "boundary" in pdict:
                pdict["boundary"] = pdict["boundary"].encode("utf-8")

            form_data = request.form.to_dict(flat=False)
            if "payload" not in form_data:
                log.error("Payload not found in form data")
                return None, None

            payload = json.loads(form_data["payload"][0])
            # Determine media manager type from headers or payload
            manager_type = request.headers.get("X-Media-Manager", "plex")
            return manager_type, payload

        # Try to parse raw data as JSON if no content type matches
        try:
            payload = json.loads(request.get_data(as_text=True))
            return "jellyfin", payload
        except json.JSONDecodeError:
            log.error("Unsupported content type: %s", content_type)
            return None, None

    except Exception as e:
        log.error("Error parsing webhook data: %s", e)
        return None, None


def register_routes(app: Flask) -> None:
    """
    Register all routes for the application.

    Args:
        app: The Flask application instance
    """

    @app.route("/webhook/<manager_type>", methods=["POST"])
    def webhook(manager_type: str) -> Response:
        """
        Handle webhooks from media managers.

        Args:
            manager_type: The type of media manager (plex, jellyfin, emby)

        Returns:
            Response: The response indicating the result of handling the webhook
        """
        # Parse webhook data
        parsed_manager_type, webhook_data = parse_webhook_data()
        if webhook_data is None:
            return make_response("", 204)

        # Get media manager
        manager_class = app.config["MEDIA_MANAGERS"].get(manager_type)
        if manager_class is None:
            log.error("Unsupported media manager: %s", manager_type)
            return make_response("", 204)

        manager = manager_class()

        # Parse media information
        media_info = manager.parse_webhook(webhook_data)
        if media_info is None:
            return make_response("", 204)

        # Get user information
        user_id = media_info.get("user_id")
        if user_id is None:
            log.error("User ID not found in webhook data")
            return make_response("", 204)

        # Get user's tracking services
        user_services = app.config["SERVICE_INSTANCES"].get(user_id)
        if not user_services:
            log.error("No tracking services configured for user: %s", user_id)
            return make_response("", 204)

        # Extract media details
        media_details = manager.extract_media_details(media_info)
        if not media_details:
            log.error(
                "No media details found for: %s", media_info.get("title")
            )
            return make_response("", 204)

        # Mark as watched in each tracking service
        for service in user_services.values():
            try:
                if media_info["type"] == "show":
                    if isinstance(service, TrackTVService):
                        service.watch_episode(
                            episode_id=media_details["tvdb"],
                            show_title=media_details["show_title"],
                            season=media_details["season"],
                            episode=media_details["episode"],
                            year=media_details["year"],
                            tmdb_id=media_details["tmdb"],
                            imdb_id=media_details["imdb"],
                        )
                    else:
                        # For TVTime and other services that only need TVDB ID
                        service.watch_episode(media_details["tvdb"])
                else:
                    # Different services expect different parameters
                    if isinstance(service, TrackTVService):
                        service.watch_movie(
                            tmdb_id=media_details["tmdb"],
                            imdb_id=media_details["imdb"],
                            movie_title=media_info.get("title"),
                        )
                    else:
                        # For TVTime and other services that only need TVDB ID
                        service.watch_movie(
                            movie_id=media_details["tvdb"],
                            movie_title=media_info.get("title"),
                            tmdb_id=media_details.get("tmdb"),
                            imdb_id=media_details.get("imdb"),
                        )
            except Exception as e:
                log.error(
                    "Error updating %s: %s", service.__class__.__name__, e
                )

        return make_response("OK", 200)
