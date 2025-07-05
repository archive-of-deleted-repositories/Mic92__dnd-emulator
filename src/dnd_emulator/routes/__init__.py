"""HTTP routes for the D&D Emulator."""

from flask import Flask

from .api import register_api_routes
from .main import register_main_routes


def register_routes(app: Flask) -> None:
    """Register all HTTP routes."""
    register_main_routes(app)
    register_api_routes(app)
