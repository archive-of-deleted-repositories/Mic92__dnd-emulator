# D&D Emulator

A web-based Dungeons & Dragons emulator with Claude as the Game Master.

![D&D Emulator Screenshot](https://github.com/Mic92/dnd-emulator/releases/download/assets/dnd-webview.png)

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

2. Install dependencies:

   ```bash
   uv sync                        # Python dependencies
   npm --prefix frontend install  # Frontend dependencies (creates package-lock.json)
   ```

### Running the Application

Run both the backend and frontend development servers with a single command:

```bash
nix develop -c process-compose
```

This starts:
- Backend (Flask) on http://localhost:5000
- Frontend (React) on http://localhost:3000

The frontend development server automatically proxies API requests to the backend.

### Tools

- **uv**: Python package management
- **ruff**: Python linting and formatting
- **mypy**: Python type checking

### Commands

- `uv sync` - Install dependencies
- `nix develop -c process-compose` - Run the app (both backend and frontend)
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

### Production Build

To build the frontend for production:

```bash
cd frontend
npm run build
```

This creates a production build in `static/dist/` that will be automatically served by Flask.
