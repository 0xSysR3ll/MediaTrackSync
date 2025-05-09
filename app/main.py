"""
Main entry point for the Plex TVTime Integration application.
"""

import os

from app import create_app

from .utils.logger import setup_logging


def main():
    """
    Main entry point for the application.
    """
    # Setup logging
    setup_logging()

    # Create Flask app
    app = create_app()

    # Get port from environment or use default
    port = int(os.environ.get("PORT", 5000))

    # Run the app
    app.run(host="0.0.0.0", port=port)


if __name__ == "__main__":
    main()
