"""Main Flask application for D&D Emulator."""

import logging

from dnd_emulator.app_factory import create_app
from dnd_emulator.routes import register_routes
from dnd_emulator.socket_handlers import register_socket_handlers

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Create app and socketio
app, socketio = create_app()

# Register routes and handlers
register_routes(app)
register_socket_handlers(socketio)
