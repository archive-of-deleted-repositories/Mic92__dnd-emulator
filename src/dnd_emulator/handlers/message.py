"""Message handler for WebSocket events."""

import asyncio
import logging
from typing import TYPE_CHECKING, Any, cast

from flask import current_app
from flask_socketio import emit

if TYPE_CHECKING:
    from dnd_emulator.app_types import DnDApp

logger = logging.getLogger(__name__)


def handle_message(data: dict[str, Any]) -> None:
    """Handle incoming player messages."""
    message = data.get("message", "")
    session_id = data.get("session_id")

    if not session_id:
        emit(
            "error",
            {
                "message": "No session selected. Create or select a session first.",
            },
        )
        return

    logger.info("Received message from session %s: %s", session_id, message)

    # Cast once at the beginning
    app = cast("DnDApp", current_app)

    # Set the session for the GM
    app.gm.set_session(session_id)

    # Run async GM response in thread
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    try:
        # Get GM response - Claude maintains all context and history
        gm_response = loop.run_until_complete(
            app.gm.send_message(message, context=None),
        )

        # Parse for dice rolls
        parsed_response = app.gm.parse_dice_rolls(gm_response)

        # Emit response
        emit(
            "gm_response",
            {
                "response": parsed_response["response"],
                "dice_rolls": parsed_response["dice_rolls"],
                "session_id": session_id,
            },
        )

    except RuntimeError as e:
        emit("error", {"message": f"Error: {e!s}"})
    finally:
        loop.close()
