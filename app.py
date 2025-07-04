"""Main Flask application for D&D Emulator."""

import asyncio
import os
import random
from typing import Any

from dotenv import load_dotenv
from flask import Flask, render_template
from flask_cors import CORS
from flask_socketio import SocketIO, emit

from game.claude_gm import ClaudeGM

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-key")

# Initialize CORS
CORS(app)

# Initialize SocketIO
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="threading")

# Game sessions storage (in-memory for now)
# Each session will have its own GM instance
game_sessions: dict[str, dict[str, Any]] = {}


@app.route("/")
def index() -> str:
    """Serve the main game interface."""
    return str(render_template("index.html"))


@socketio.on("connect")
def handle_connect() -> None:
    """Handle client connection."""
    emit("connected", {"status": "Connected to D&D Emulator"})


@socketio.on("disconnect")
def handle_disconnect() -> None:
    """Handle client disconnection."""
    # Note: In production, you'd want to track which session_id belongs to which client
    # and clean up the GM instance when the last client disconnects


@socketio.on("send_message")
def handle_message(data: dict[str, Any]) -> None:
    """Handle incoming player messages."""
    message = data.get("message", "")
    session_id = data.get("session_id", "default")

    # Get or create session
    if session_id not in game_sessions:
        game_sessions[session_id] = {
            "history": [],
            "game_state": {
                "players": [],
                "current_scene": "Tavern",
                "initiative_order": [],
            },
            "gm": ClaudeGM(),  # Create GM instance for this session
        }

    session = game_sessions[session_id]
    gm = session["gm"]

    # Add message to history
    session["history"].append(f"Player: {message}")

    # Run async GM response in thread
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    try:
        # Get GM response
        gm_response = loop.run_until_complete(
            gm.send_message(message, context=session),
        )

        # Parse for dice rolls
        parsed_response = gm.parse_dice_rolls(gm_response)

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


@socketio.on("roll_dice")
def handle_dice_roll(data: dict[str, Any]) -> None:
    """Handle dice roll requests."""
    notation = data.get("notation", "1d20")

    # Parse dice notation (simplified)
    try:
        parts = notation.lower().split("d")
        num_dice = int(parts[0])

        if "+" in parts[1]:
            die_parts = parts[1].split("+")
            die_size = int(die_parts[0])
            modifier = int(die_parts[1])
        elif "-" in parts[1]:
            die_parts = parts[1].split("-")
            die_size = int(die_parts[0])
            modifier = -int(die_parts[1])
        else:
            die_size = int(parts[1])
            modifier = 0

        # Roll dice
        rolls = [random.randint(1, die_size) for _ in range(num_dice)]  # noqa: S311
        total = sum(rolls) + modifier

        emit(
            "dice_result",
            {
                "notation": notation,
                "rolls": rolls,
                "modifier": modifier,
                "total": total,
            },
        )

    except (ValueError, IndexError) as e:
        emit("error", {"message": f"Invalid dice notation: {e!s}"})


async def cleanup_sessions() -> None:
    """Clean up all GM sessions."""
    for session in game_sessions.values():
        if "gm" in session:
            await session["gm"].stop_session()


if __name__ == "__main__":
    try:
        socketio.run(
            app, debug=True, host="127.0.0.1", port=5000, allow_unsafe_werkzeug=True,
        )
    finally:
        # Clean up sessions on shutdown
        loop = asyncio.new_event_loop()
        loop.run_until_complete(cleanup_sessions())
        loop.close()
