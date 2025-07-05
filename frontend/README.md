# D&D Emulator Frontend

React TypeScript frontend for the D&D Emulator application.

## Development

```bash
# Install dependencies
npm install

# Start development server (runs on port 3000)
npm run dev
```

The development server proxies API and WebSocket requests to the Flask backend on port 5000.

## Production Build

```bash
# Build for production
npm run build
```

This creates a production build in `../static/dist/` that will be served by Flask.

## Technologies

- React 18 with TypeScript
- Socket.IO Client for real-time communication
- Vite for fast development and building