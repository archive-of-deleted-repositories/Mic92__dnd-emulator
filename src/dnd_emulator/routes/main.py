"""Main page routes."""

from flask import Flask, render_template


def register_main_routes(app: Flask) -> None:
    """Register main page routes."""

    @app.route("/")
    def index() -> str:
        """Serve the main game interface."""
        return str(render_template("index.html"))
