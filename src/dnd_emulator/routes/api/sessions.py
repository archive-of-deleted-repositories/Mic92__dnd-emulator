"""Session management API routes."""

import logging
from typing import TYPE_CHECKING, Any, cast

from flask import Flask, current_app, jsonify

if TYPE_CHECKING:
    from dnd_emulator.app_types import DnDApp

logger = logging.getLogger(__name__)


def register_session_routes(app: Flask) -> None:
    """Register session-related API routes."""

    @app.route("/api/sessions")
    def list_sessions() -> tuple[Any, int]:
        """List all available Claude sessions."""
        try:
            app = cast("DnDApp", current_app)
            sessions = app.session_manager.list_sessions()
            return jsonify({"sessions": sessions}), 200
        except Exception as e:
            logger.exception("Error listing sessions")
            return jsonify({"error": str(e)}), 500

    @app.route("/api/sessions/<session_id>")
    def get_session(session_id: str) -> tuple[Any, int]:
        """Get details for a specific session."""
        app = cast("DnDApp", current_app)
        if app.session_manager.session_exists(session_id):
            session_path = app.session_manager.get_session_file_path(session_id)
            return jsonify(
                {
                    "session_id": session_id,
                    "exists": True,
                    "path": str(session_path),
                },
            ), 200
        return jsonify({"session_id": session_id, "exists": False}), 404
