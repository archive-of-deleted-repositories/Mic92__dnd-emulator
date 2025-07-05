"""Register socket handlers."""

from flask_socketio import SocketIO

from .handlers import (
    handle_connect,
    handle_dice_roll,
    handle_disconnect,
    handle_message,
    handle_session_switch,
)


def register_socket_handlers(socketio: SocketIO) -> None:
    """Register all socket event handlers."""
    socketio.on("connect")(handle_connect)
    socketio.on("disconnect")(handle_disconnect)
    socketio.on("send_message")(handle_message)
    socketio.on("roll_dice")(handle_dice_roll)
    socketio.on("switch_session")(handle_session_switch)
