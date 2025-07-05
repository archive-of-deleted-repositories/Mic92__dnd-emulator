"""Type definitions for the Flask app."""

from flask import Flask

from dnd_emulator.game.claude_gm import ClaudeGM
from dnd_emulator.game.session_manager import ClaudeSessionManager


class DnDApp(Flask):
    """Flask app with D&D-specific attributes."""

    gm: ClaudeGM
    session_manager: ClaudeSessionManager
