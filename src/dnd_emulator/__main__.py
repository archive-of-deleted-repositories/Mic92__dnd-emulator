"""Main entry point for D&D Emulator."""

from dnd_emulator.app import app, socketio


def main() -> None:
    """Run the D&D Emulator application."""
    socketio.run(
        app, debug=True, host="127.0.0.1", port=5000, allow_unsafe_werkzeug=True,
    )


if __name__ == "__main__":
    main()
