"""Main Flask application for D&D Emulator."""

import asyncio
import logging
import os
import random
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from flask import Flask, jsonify, render_template
from flask_cors import CORS
from flask_socketio import SocketIO, emit

from dnd_emulator.game.claude_gm import ClaudeGM
from dnd_emulator.game.session_manager import ClaudeSessionManager

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Initialize Flask app with correct paths
# Find the package root directory
package_root = Path(__file__).parent.parent.parent
template_dir = package_root / "templates"
static_dir = package_root / "static"

app = Flask(__name__, template_folder=str(template_dir), static_folder=str(static_dir))
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-key")

# Initialize CORS
CORS(app)

# Initialize SocketIO
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="threading")

# Initialize Claude GM
gm = ClaudeGM()

# Initialize Claude Session Manager
session_manager = ClaudeSessionManager()

# Game sessions storage (in-memory for now)
game_sessions: dict[str, dict[str, Any]] = {}


@app.route("/")
def index() -> str:
    """Serve the main game interface."""
    return str(render_template("index.html"))


@app.route("/api/sessions")
def list_sessions() -> tuple[Any, int]:
    """List all available Claude sessions."""
    try:
        sessions = session_manager.list_sessions()
        return jsonify({"sessions": sessions}), 200
    except Exception as e:
        logger.exception("Error listing sessions")
        return jsonify({"error": str(e)}), 500


@app.route("/api/sessions/<session_id>")
def get_session(session_id: str) -> tuple[Any, int]:
    """Get details for a specific session."""
    if session_manager.session_exists(session_id):
        session_path = session_manager.get_session_file_path(session_id)
        return jsonify(
            {
                "session_id": session_id,
                "exists": True,
                "path": str(session_path),
            },
        ), 200
    return jsonify({"session_id": session_id, "exists": False}), 404


@socketio.on("connect")
def handle_connect() -> None:
    """Handle client connection."""
    logger.info("Client connected")
    emit("connected", {"status": "Connected to D&D Emulator"})


@socketio.on("disconnect")
def handle_disconnect() -> None:
    """Handle client disconnection."""
    logger.info("Client disconnected")
    # Note: In production, you'd want to track which session_id belongs to which client
    # and clean up the GM instance when the last client disconnects


@socketio.on("send_message")
def handle_message(data: dict[str, Any]) -> None:
    """Handle incoming player messages."""
    message = data.get("message", "")
    session_id = data.get("session_id")

    logger.info("Received message from session %s: %s", session_id or "new", message)

    # Set the Claude session if provided
    if session_id and session_manager.session_exists(session_id):
        gm.set_session(session_id)
    else:
        gm.set_session(None)

    # Get or create game session context (use session_id or "new" as key)
    session_key = session_id or "new"
    if session_key not in game_sessions:
        logger.info("Creating new game session context: %s", session_key)
        game_sessions[session_key] = {
            "history": [],
            "game_state": {
                "players": [],
                "current_scene": "Tavern",
                "initiative_order": [],
            },
        }

    session = game_sessions[session_key]

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


@socketio.on("switch_session")
def handle_session_switch(data: dict[str, Any]) -> None:
    """Handle session switching requests."""
    session_id = data.get("session_id")

    if session_id and session_manager.session_exists(session_id):
        # This is a Claude session - tell the GM to use it
        logger.info("Switching to Claude session: %s", session_id)
        gm.set_session(session_id)
        emit("session_switched", {"session_id": session_id})
    else:
        # New session (no specific Claude session)
        logger.info("Starting new session")
        gm.set_session(None)
        emit("session_switched", {"session_id": None})
