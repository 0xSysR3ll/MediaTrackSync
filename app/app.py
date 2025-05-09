"""
This module contains the implementation of a webhook for media tracking integration.

Author: 0xsysr3ll
Copyright: © 2024 0xsysr3ll. All rights reserved.
License: see the LICENSE file.

"""

import os
from typing import Dict, Type

from flask import Flask

# Import media managers
from .managers.plex import PlexManager
from .routes import register_routes
from .services.tracktv import TrackTVService

# Import tracking services
from .services.tvtime import TVTimeService
from .utils.config import Config
from .utils.logger import logging as log

# from managers.jellyfin import JellyfinManager
# from managers.emby import EmbyManager


def create_app(config_path: str = "config/config.yml") -> Flask:
    """
    Create and configure the Flask application.

    Args:
        config_path: Path to the configuration file

    Returns:
        Flask: The configured Flask application
    """
    app = Flask(__name__)
    app.secret_key = os.urandom(24)
    app.logger.setLevel(log.ERROR)

    # Load configuration
    config = Config(config_path)
    config.load()

    # Initialize tracking services
    tracking_services: Dict[str, Type] = {
        "tvtime": TVTimeService,
        "tracktv": TrackTVService,
    }

    # Initialize media managers
    media_managers: Dict[str, Type] = {
        "plex": PlexManager,
    }

    # Initialize service instances for each user
    service_instances = {}
    for user, user_config in config.get_config_of("users").items():
        user_services = {}

        # Initialize tracking services for this user
        for service_name, service_class in tracking_services.items():
            if service_name in user_config:
                try:
                    if service_name == "tracktv":
                        service = service_class(
                            client_id=user_config[service_name]["client_id"],
                            client_secret=user_config[service_name][
                                "client_secret"
                            ],
                            code=user_config[service_name]["code"],
                            redirect_uri=user_config[service_name][
                                "redirect_uri"
                            ],
                        )
                    else:
                        service = service_class(
                            username=user_config[service_name]["username"],
                            password=user_config[service_name]["password"],
                        )
                    service.login()
                    user_services[service_name] = service
                except KeyError as e:
                    log.error(
                        "Error initializing %s for user %s: %s",
                        service_name,
                        user,
                        e,
                    )
                    continue

        service_instances[user] = user_services

    # Store service instances in app context
    app.config["SERVICE_INSTANCES"] = service_instances
    app.config["MEDIA_MANAGERS"] = media_managers

    # Register routes
    register_routes(app)

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=5000, debug=False)
