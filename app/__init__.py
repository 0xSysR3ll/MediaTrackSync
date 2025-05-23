"""
Plex TVTime Integration

A webhook-based integration between Plex and various media tracking services.
"""

from .app import create_app

__version__ = "1.0.0"
__all__ = ["create_app"]
