"""Connection handlers for WebSocket events."""

import logging

from flask_socketio import emit

logger = logging.getLogger(__name__)


def handle_connect() -> None:
    """Handle client connection."""
    logger.info("Client connected")
    emit("connected", {"status": "Connected to D&D Emulator"})


def handle_disconnect() -> None:
    """Handle client disconnection."""
    logger.info("Client disconnected")
    # Note: In production, you'd want to track which session_id belongs to which client
    # and clean up the GM instance when the last client disconnects
