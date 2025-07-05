"""API routes module."""

from flask import Flask

from .sessions import register_session_routes


def register_api_routes(app: Flask) -> None:
    """Register all API routes."""
    register_session_routes(app)
