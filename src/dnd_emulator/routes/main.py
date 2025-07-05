"""Main page routes."""

from pathlib import Path

from flask import Flask, Response, send_from_directory


def register_main_routes(app: Flask) -> None:
    """Register main page routes."""

    @app.route("/")
    def index() -> Response:
        """Serve the React app."""
        static_dir = Path(app.static_folder or "")
        return send_from_directory(str(static_dir / "dist"), "index.html")

    @app.route("/assets/<path:path>")
    def serve_assets(path: str) -> Response:
        """Serve React assets."""
        static_dir = Path(app.static_folder or "")
        return send_from_directory(str(static_dir / "dist" / "assets"), path)
