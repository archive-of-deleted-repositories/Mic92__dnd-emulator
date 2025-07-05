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

    logger.info("Received message from session %s: %s", session_id or "new", message)

    # Cast once at the beginning
    app = cast("DnDApp", current_app)

    # Set the Claude session if provided
    if session_id and app.session_manager.session_exists(session_id):
        app.gm.set_session(session_id)
    else:
        app.gm.set_session(None)

    # Get or create game session context (use session_id or "new" as key)
    session_key = session_id or "new"
    if session_key not in app.game_sessions:
        logger.info("Creating new game session context: %s", session_key)
        app.game_sessions[session_key] = {
            "history": [],
            "game_state": {
                "players": [],
                "current_scene": "Tavern",
                "initiative_order": [],
            },
        }

    session = app.game_sessions[session_key]

    # Add message to history
    session["history"].append(f"Player: {message}")

    # Run async GM response in thread
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    try:
        # Get GM response
        gm_response = loop.run_until_complete(
            app.gm.send_message(message, context=session),
        )

        # Parse for dice rolls
        parsed_response = app.gm.parse_dice_rolls(gm_response)

        # Add to history
        session["history"].append(f"GM: {gm_response}")

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
