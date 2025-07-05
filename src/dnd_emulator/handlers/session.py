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

    if not session_id:
        emit("error", {"message": "Session name is required"})
        return

    # Cast once at the beginning
    app = cast("DnDApp", current_app)

    # Set the session for the GM (creates directory if needed)
    logger.info("Switching to session: %s", session_id)
    app.gm.set_session(session_id)
    emit("session_switched", {"session_id": session_id})
