# Toy Robot Simulator

A simulation web-app of multiple toy robots moving on a configurable table top.

## Stack

- **Python core** (`/core`): pure logic, no I/O, no framework dependencies
- **Pytest** (`/tests`): unit tests against core data models
- **FastAPI** (`/api`): stateless REST API wrapping the core
- **TypeScript + React + Vite + Tailwind** (`/ui`): prototype UI

## Quick Start

```bash
make install
```

```bash
make server
```
The API runs at `http://localhost:8000`.

```bash
make client
```
The UI runs at `http://localhost:5173`.

There is also a VSCode compound launch config `Launch TableTopBots` in `launch.json` which launches both of these. 

### Tests

```bash
make test
```

## API Endpoints

| Method | Path          | Description                           |
| ------ | ------------- | ------------------------------------- |
| POST   | `/simulate`   | Run full simulation, return snapshots |
| POST   | `/validate`   | Validate a single command string      |
| POST   | `/parse-file` | Parse a `.txt` command file           |
