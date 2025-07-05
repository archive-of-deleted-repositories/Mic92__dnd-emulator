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

### Commands

- `uv sync` - Install dependencies
- `uv run python app.py` - Run the app
- `ruff check --fix --unsafe-fixes .` - Lint Python code
- `ruff format .` - Format python code
- `uv run mypy .` - Type check Python code

## Architecture

- **Backend**: Python Flask with Flask-SocketIO for WebSocket support
- **Claude Integration**: CLI wrapper for Claude as Game Master
- **Frontend**: React TypeScript application with Socket.IO client

## Frontend Development

The frontend is a React TypeScript application located in the `frontend/` directory.

### Setup

1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Start the development server (runs on port 3000):
   ```bash
   npm run dev
   ```

### Production Build

To build the frontend for production:

```bash
cd frontend
npm run build
```

This creates a production build in `static/dist/` that will be automatically served by Flask.
