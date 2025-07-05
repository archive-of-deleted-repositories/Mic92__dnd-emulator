"""Flask application factory."""

import os
from pathlib import Path

from flask_cors import CORS
from flask_socketio import SocketIO

from dnd_emulator.app_types import DnDApp
from dnd_emulator.game.claude_gm import ClaudeGM
from dnd_emulator.game.session_manager import ClaudeSessionManager


def create_app() -> tuple[DnDApp, SocketIO]:
    """Create and configure the Flask application.

    Returns:
        Tuple of (Flask app, SocketIO instance)

    """
    # Find the package root directory
    package_root = Path(__file__).parent.parent.parent
    template_dir = package_root / "templates"
    static_dir = package_root / "static"

    # Create Flask app
    app = DnDApp(
        __name__,
        template_folder=str(template_dir),
        static_folder=str(static_dir),
    )
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-key")

    # Initialize CORS
    CORS(app)

    # Initialize SocketIO
    socketio = SocketIO(app, cors_allowed_origins="*", async_mode="threading")

    # Initialize game components and store in app context
    app.gm = ClaudeGM()
    app.session_manager = ClaudeSessionManager()

    return app, socketio
