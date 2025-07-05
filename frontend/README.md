# D&D Emulator Frontend

React TypeScript frontend for the D&D Emulator application.

## Development

```bash
# Install dependencies
npm install

# Start development server (runs on port 3000)
npm run dev

# Run linting and formatting checks
npm run lint

# Fix linting and formatting issues automatically
npm run lint:fix
```

The development server proxies API and WebSocket requests to the Flask backend on port 5000.

## Code Quality

This project uses ESLint with TypeScript support and Prettier for code formatting. The ESLint configuration includes:
- TypeScript type checking
- React best practices and hooks rules
- Prettier integration for consistent formatting

All linting and formatting is handled through ESLint, so you only need to use the `lint` and `lint:fix` commands.

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