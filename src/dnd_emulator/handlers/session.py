"""Session management handler for WebSocket events."""

import logging
from typing import TYPE_CHECKING, Any, cast

from flask import current_app
from flask_socketio import emit

if TYPE_CHECKING:
    from dnd_emulator.app_types import DnDApp

logger = logging.getLogger(__name__)


def handle_session_switch(data: dict[str, Any]) -> None:
    """Handle session switching requests."""
    session_id = data.get("session_id")

    # Cast once at the beginning
    app = cast("DnDApp", current_app)

    if session_id and app.session_manager.session_exists(session_id):
        # This is a Claude session - tell the GM to use it
        logger.info("Switching to Claude session: %s", session_id)
        app.gm.set_session(session_id)
        emit("session_switched", {"session_id": session_id})
    else:
        # New session (no specific Claude session)
        logger.info("Starting new session")
        app.gm.set_session(None)
        emit("session_switched", {"session_id": None})
