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

    # Allow null session_id for "New Session" (will require name when sending messages)
    if session_id == "":
        session_id = None

    # Cast once at the beginning
    app = cast("DnDApp", current_app)

    if session_id:
        # Set the session for the GM (creates directory if needed)
        logger.info("Switching to session: %s", session_id)
        app.gm.set_session(session_id)
    else:
        logger.info("Cleared session selection")

    emit("session_switched", {"session_id": session_id})
