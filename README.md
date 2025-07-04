# D&D Emulator

A web-based Dungeons & Dragons emulator with Claude as the Game Master.

## Features

- Interactive D&D gameplay with Claude AI as the Game Master
- Real-time WebSocket communication
- Dice rolling system
- Session management
- Web-based interface

## Development

This project uses Nix flakes for development environment management.

### Setup

1. Enter the development shell:

   ```bash
   nix develop
   ```

2. Install Python dependencies:

   ```bash
   uv sync
   ```

3. Run the application:
   ```bash
   uv run python app.py
   ```

### Tools

- **uv**: Python package management
- **ruff**: Python linting and formatting
- **mypy**: Python type checking
- **treefmt**: Multi-language code formatting

### Commands

- `uv sync` - Install dependencies
- `uv run python app.py` - Run the app
- `treefmt` - Format all files
- `ruff check .` - Lint Python code
- `mypy .` - Type check Python code

## Architecture

- **Backend**: Python Flask with Flask-SocketIO for WebSocket support
- **Claude Integration**: CLI wrapper for Claude as Game Master
- **Frontend**: HTML/CSS/JavaScript with Socket.IO client
