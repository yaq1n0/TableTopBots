# Toy Robot Simulator — UI

React + TypeScript + Vite + Tailwind frontend for the Toy Robot Simulator.

## Quick Start

```bash
npm install
npm run dev
```

The UI runs at `http://localhost:5173`. The backend must also be running at `http://localhost:8000` — see the root `README.md`.

## OpenAPI Pipeline

Types are generated directly from the FastAPI backend's OpenAPI schema. Pydantic models are the single source of truth: changes to `core/models.py` flow through to TypeScript automatically.

```
core/models.py  →  FastAPI /openapi.json  →  src/generated/api.d.ts  →  src/types.ts
```

### Regenerating types

Requires the backend to be running:

```bash
npm run openapi:generate
```

This writes `src/generated/api.d.ts`. Never edit that file manually — it will be overwritten.

### Type-checking after generation

```bash
npm run openapi:check
```

### When to regenerate

Re-run `openapi:generate` after any change to the Pydantic models in `core/models.py` or the endpoint signatures in `api/main.py`.

## Project Structure

```
src/
├── generated/
│   └── api.d.ts          # Auto-generated from OpenAPI — do not edit
├── components/
│   ├── BoardGrid.tsx      # Grid display with obstacle and robot overlays
│   ├── ErrorBanner.tsx    # Error message display
│   ├── RobotPanel.tsx     # Per-robot setup (command input) and run (result) views
│   ├── SetupPanel.tsx     # Board config, obstacles, robots, run button
│   └── Timeline.tsx       # Turn navigation controls
├── hooks/
│   ├── useSetup.ts        # Setup phase state: board size, obstacles, robots, run
│   └── usePlayback.ts     # Run phase state: response, current turn, navigation
├── api.ts                 # openapi-fetch client (typed against generated schema)
├── types.ts               # Re-exports from generated/api.d.ts
├── validation.ts          # Client-side command regex validation
└── App.tsx                # Phase switching and layout
```

## Scripts

| Command | Description |
|---------|-------------|
| `npm run dev` | Start Vite dev server |
| `npm run build` | Type-check and build for production |
| `npm run lint` | Run ESLint |
| `npm run format` | Format with Prettier |
| `npm run openapi:generate` | Regenerate types from live backend (backend must be running) |
| `npm run openapi:check` | Type-check the project |
