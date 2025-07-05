"""Socket handlers for the D&D Emulator."""

from .connection import handle_connect, handle_disconnect
from .dice import handle_dice_roll
from .message import handle_message
from .session import handle_session_switch

__all__ = [
    "handle_connect",
    "handle_dice_roll",
    "handle_disconnect",
    "handle_message",
    "handle_session_switch",
]
