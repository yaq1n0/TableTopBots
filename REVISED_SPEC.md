# Toy Robot Simulator

## Overview

A simulation web-app of multiple toy robots moving on a configurable table top. This is a superset of the original single-robot spec — all original behaviors are preserved.

**Stack:**

- **Python core** (`/core`): pure logic with strong pydantic typing, no I/O, no framework dependencies
- **Pytest** (`/tests`): comprehensive unit tests against core data models for core logic
- **FastAPI** (`/api`): stateless REST API wrapping the core
- **TypeScript + React + Vite + Tailwind** (`/ui`): prototype UI

## Data Models

All models use these exact field names. Python side: Pydantic `BaseModel` subclasses. TypeScript side: matching interfaces.

### Direction (enum)

```
NORTH | SOUTH | EAST | WEST
```

### Command

```python
class Command(BaseModel):
    type: Literal["PLACE", "MOVE", "LEFT", "RIGHT", "REPORT"]
    # PLACE only:
    x: int | None = None
    y: int | None = None
    facing: Direction | None = None
    # MOVE N, LEFT N, RIGHT N:
    count: int = 1
```

Parsing rules:
- `PLACE 2,3,NORTH` → `Command(type="PLACE", x=2, y=3, facing=NORTH)`
- `MOVE` → `Command(type="MOVE", count=1)`
- `MOVE 5` → `Command(type="MOVE", count=5)`
- `LEFT` → `Command(type="LEFT", count=1)`
- `LEFT 3` → `Command(type="LEFT", count=3)`
- `RIGHT` → `Command(type="RIGHT", count=1)`
- `RIGHT 2` → `Command(type="RIGHT", count=2)`
- `REPORT` → `Command(type="REPORT")`

### RobotState

```python
class RobotState(BaseModel):
    name: str
    x: int
    y: int
    facing: Direction
    placed: bool  # False until first successful PLACE
```

### CommandResult

```python
class CommandResult(BaseModel):
    robot_name: str
    command: Command | None        # None if this robot had no command this turn
    executed: bool                  # True if command was applied, False if blocked/skipped
    reason: str | None = None      # Why it was blocked, e.g. "collision with robot B at (3,2)"
    output: str | None = None      # REPORT output, e.g. "3,3,NORTH"
```

### Snapshot

```python
class Snapshot(BaseModel):
    turn: int                          # 0 = initial placements, 1..N = subsequent turns
    robots: list[RobotState]           # State of ALL robots after this turn resolves
    results: list[CommandResult]       # One per robot, in robot-addition order
```

### SimulationRequest

```python
class SimulationRequest(BaseModel):
    width: int = 5                                          # Board width (valid x: 0..width-1)
    height: int = 5                                         # Board height (valid y: 0..height-1)
    obstacles: dict[str, list[tuple[int, int]]] = {}        # obstacle_name → list of (x,y) cells
    robot_names: list[str]                                  # Ordered list of robot names
    command_stacks: list[list[str | None]]                  # command_stacks[robot_index][turn_index]
```

`command_stacks` is a list of equal-length arrays (one per robot). Each entry is either a command string (e.g. `"MOVE"`, `"PLACE 1,2,EAST"`) or `null` (skip this turn). The core parses strings into `Command` objects. The UI/API is responsible for padding shorter stacks with `null` so all stacks have the same length before sending.

### SimulationResponse

```python
class SimulationResponse(BaseModel):
    snapshots: list[Snapshot]   # Ordered list, index 0 = turn 0, index N = turn N
```

## Session Lifecycle

A session follows a strict phase order: **Setup → Run**.

### Setup Phase

1. **Board config**: specify dimensions (W, H) and optional obstacles. Default: 5x5, no obstacles. Obstacles are added by typing an obstacle name and clicking cells on the grid to toggle which cells belong to that obstacle.
2. **Add robots**: add one or more named robots. Each robot is added either by:
   - Clicking "Add Robot" in the UI, which creates a robot with an empty command stack (the user types commands into the per-robot command editor).
   - Clicking "Import File" on a robot, which loads commands from a `.txt` file (one command per line) into that robot's command stack.
3. **Lock & Run**: once the user clicks "Run", the setup is locked — no new robots or obstacles can be added. The UI pads all command stacks to equal length with `null`, sends the `SimulationRequest` to `POST /simulate`, and populates the timeline with the returned snapshots.

### Run Phase

The UI displays the simulation results. The user can:
- Step forward/backward through turns using the timeline scrubber
- See each robot's position and facing on the grid at each turn
- See per-robot command results (executed/blocked/output) in robot panels
- Click "Reset" to return to the Setup phase

## Commands

Each robot has its own independent command stack. Commands do not include the robot name — the robot is identified by its index in the `command_stacks` array.

- `PLACE X,Y,F` — Place/teleport the robot to (X,Y) facing F. Must be the first command for each robot. Blocked if the target cell is occupied by another robot or an obstacle.
- `MOVE` — Move 1 unit forward in the robot's facing direction. Blocked if the target cell is off the board, occupied by another robot, or an obstacle.
- `MOVE N` — Move up to N units forward. The robot advances cell-by-cell; if any cell is blocked, the robot stops at the last valid cell. If the first cell is blocked, the robot doesn't move.
- `LEFT` — Rotate 90 degrees counter-clockwise.
- `LEFT N` — Rotate N x 90 degrees counter-clockwise.
- `RIGHT` — Rotate 90 degrees clockwise.
- `RIGHT N` — Rotate N x 90 degrees clockwise.
- `REPORT` — No state change. Populates the `output` field of this robot's `CommandResult` with `"X,Y,FACING"` (e.g. `"3,3,NORTH"`).

Direction cycle: `NORTH → (RIGHT) → EAST → SOUTH → WEST → NORTH`. Left is the reverse.

## Turn Resolution

Simulation is turn-based. Each turn, every robot receives exactly one command (or `null` to skip).

**Resolution order: sequential by robot-addition order.** On each turn, robots resolve one at a time in the order they were added. Each robot's command resolves against the **current** board state (which includes the results of all prior robots' commands in that same turn). This means:

- If robot A moves out of cell (1,0) and robot B (resolving after A) tries to PLACE at (1,0), B succeeds — the cell is now empty.
- If robot A moves into cell (3,2) where robot B currently sits, A is blocked — even if B will move away later in this turn (B hasn't resolved yet).

## Rules

- The origin (0,0) is the SOUTH WEST corner.
- Valid coordinates: `0 <= x < width`, `0 <= y < height`.
- The first command for each robot must be a `PLACE` command. All commands before the first successful PLACE are ignored (result: `executed=False, reason="robot not placed"`).
- After a valid PLACE, any command may be issued in any order, including another PLACE.
- PLACE to an occupied cell (another robot or obstacle) is blocked.
- MOVE off the board edge is blocked. MOVE into an occupied cell is blocked.
- MOVE N advances cell-by-cell, stopping before the first blocked cell.
- LEFT and RIGHT always succeed (they don't change position).
- REPORT always succeeds for placed robots (no state change, just output).
- `null` command: robot does nothing, `executed=False, reason="no command"`.
- Unplaced robot receiving any non-PLACE command: `executed=False, reason="robot not placed"`.

## File Input

Robot command sequences can be imported from `.txt` files via the UI. Each file contains one command per line for a single robot. The file is assumed valid (starts with PLACE, well-formed commands). No validation is performed on file imports — happy-path parsing only.

## Input Validation

- **File import**: assumed valid, no validation.
- **UI command editor**: each command typed in the UI is validated client-side before being added to the stack. Validation checks syntax only (matches command grammar), not simulation-level rules (collisions, board bounds, etc.). Simulation-level validation happens at runtime in the core.

Validation function signature:
```python
def is_valid_command(command_str: str) -> bool
```
```typescript
function isValidCommand(command: string): boolean
```

Accepts: `PLACE X,Y,F`, `MOVE`, `MOVE N`, `LEFT`, `LEFT N`, `RIGHT`, `RIGHT N`, `REPORT` (case-insensitive, X/Y/N are non-negative integers, F is a valid direction). Rejects everything else.

## API Endpoints

All endpoints return JSON. Errors return HTTP 422 with `{"detail": "description of the error"}`.

### `POST /simulate`

**Request body**: `SimulationRequest` (JSON)

**Response body**: `SimulationResponse` (JSON)

Runs the full simulation and returns all snapshots. The API parses command strings into `Command` objects, calls the core engine, and returns the result. Assumes valid input (no validation beyond what Pydantic provides).

### `POST /validate`

**Request body**: `{"command": "MOVE 3"}`

**Response body**: `{"valid": true}` or `{"valid": false, "error": "Invalid command format"}`

Validates a single command string syntactically.

### `POST /parse-file`

**Request body**: multipart file upload (`.txt` file)

**Response body**: `{"commands": ["PLACE 0,0,NORTH", "MOVE", "REPORT"]}`

Parses a `.txt` file (one command per line) and returns the list of command strings. No validation — assumes the file is well-formed.

### `GET /health`

**Response body**: `{"status": "ok"}`

## Architecture

```
project root/
├── core/
│   ├── __init__.py
│   ├── models.py        # Pydantic models (Command, RobotState, Snapshot, etc.)
│   ├── engine.py         # simulate(request: SimulationRequest) -> SimulationResponse
│   └── parsing.py        # parse_command(s: str) -> Command, is_valid_command(s: str) -> bool
├── tests/
│   ├── __init__.py
│   ├── test_parsing.py   # Test command parsing
│   ├── test_engine.py    # Test simulation scenarios (single robot, multi-robot, obstacles, edge cases)
│   └── test_models.py    # Test model validation if needed
├── api/
│   ├── __init__.py
│   └── main.py           # FastAPI app with /simulate, /validate, /parse-file, /health
├── ui/
│   ├── package.json
│   ├── tsconfig.json
│   ├── vite.config.ts
│   ├── index.html
│   ├── src/
│   │   ├── main.tsx
│   │   ├── App.tsx               # Top-level: manages Setup vs Run phase
│   │   ├── types.ts              # TypeScript interfaces matching Python models
│   │   ├── api.ts                # API client (fetch wrappers for /simulate, /validate, /parse-file)
│   │   ├── validation.ts         # isValidCommand() — client-side validation
│   │   ├── components/
│   │   │   ├── SetupPanel.tsx     # Board config, obstacle editor, robot list, add/import/run buttons
│   │   │   ├── BoardGrid.tsx      # Visual grid: robots (with name labels + direction arrows), obstacles, empty cells
│   │   │   ├── RobotPanel.tsx     # Per-robot: command editor (setup) / command history with results (run)
│   │   │   └── Timeline.tsx       # Turn scrubber: prev/next buttons, turn counter, reset button
│   │   └── index.css             # Tailwind imports
│   ├── tailwind.config.js
│   └── postcss.config.js
├── requirements.txt              # fastapi, uvicorn, pydantic, pytest
├── README.md
└── REVISED_SPEC.md
```

### Core (`/core`)

The core is a **pure function**: `simulate(request: SimulationRequest) -> SimulationResponse`. Given board config, robot names, and command stacks, it produces an ordered list of snapshots. No I/O, no side effects, no server state.

The engine processes turn by turn (turn 0 through turn N). On each turn, it iterates through robots in order, resolves each command against the current board state, updates the board state, and records the result. After all robots resolve, it captures a `Snapshot`.

### API (`/api`)

FastAPI wraps the core. Stateless — receives all inputs, returns all outputs. No session storage. CORS enabled for `http://localhost:5173` (Vite dev server).

### UI (`/ui`)

React SPA. Two phases:

**Setup screen:**
- Width/Height number inputs (default 5x5)
- Obstacle editor: text input for obstacle name + click grid cells to toggle. Shows obstacle cells in a distinct color with the obstacle name label.
- Robot list: add robot (text input for name), remove robot, per-robot command editor (textarea, one command per line), import file button per robot.
- "Run Simulation" button: pads stacks, sends request, transitions to run phase.

**Run screen:**
- Board grid showing all robots at the current turn (colored circles with name label and direction arrow) and obstacles (gray cells with name label).
- Robot panels showing each robot's command and result for the current turn (command text, executed/blocked badge, reason text, REPORT output).
- Timeline: "Prev" / "Next" buttons, current turn indicator (`Turn 3 of 12`), "Reset" button to return to setup.

## Examples

All examples use a **5x5 board** (valid coordinates: 0-4 in each axis) unless noted.

### Example 1: Single robot, basic movement

```
Board: 5x5, no obstacles
Robots: [A]

Commands:
  A: PLACE 0,0,NORTH
  A: MOVE
  A: REPORT

Snapshots:
  Turn 0: A → PLACE 0,0,NORTH → executed, placed at (0,0,NORTH)
  Turn 1: A → MOVE             → executed, moved to (0,1,NORTH)
  Turn 2: A → REPORT           → executed, output "0,1,NORTH"
```

### Example 2: Single robot, turning

```
Board: 5x5, no obstacles
Robots: [A]

Commands:
  A: PLACE 0,0,NORTH
  A: LEFT
  A: REPORT

Snapshots:
  Turn 0: A → PLACE 0,0,NORTH → executed, placed at (0,0,NORTH)
  Turn 1: A → LEFT             → executed, rotated to (0,0,WEST)
  Turn 2: A → REPORT           → executed, output "0,0,WEST"
```

### Example 3: Single robot, compound movement

```
Board: 5x5, no obstacles
Robots: [A]

Commands:
  A: PLACE 1,2,EAST
  A: MOVE
  A: MOVE
  A: LEFT
  A: MOVE
  A: REPORT

Snapshots:
  Turn 0: A → PLACE 1,2,EAST → executed, placed at (1,2,EAST)
  Turn 1: A → MOVE            → executed, moved to (2,2,EAST)
  Turn 2: A → MOVE            → executed, moved to (3,2,EAST)
  Turn 3: A → LEFT            → executed, rotated to (3,2,NORTH)
  Turn 4: A → MOVE            → executed, moved to (3,3,NORTH)
  Turn 5: A → REPORT          → executed, output "3,3,NORTH"
```

### Example 4: Fall prevention

```
Board: 5x5, no obstacles
Robots: [A]

Commands:
  A: PLACE 4,4,NORTH
  A: MOVE
  A: REPORT

Snapshots:
  Turn 0: A → PLACE 4,4,NORTH → executed, placed at (4,4,NORTH)
  Turn 1: A → MOVE             → blocked, reason: "would fall off north edge", stays at (4,4,NORTH)
  Turn 2: A → REPORT           → executed, output "4,4,NORTH"
```

### Example 5: MOVE N with partial advance

```
Board: 5x5, no obstacles
Robots: [A]

Commands:
  A: PLACE 2,2,EAST
  A: MOVE 5
  A: REPORT

Snapshots:
  Turn 0: A → PLACE 2,2,EAST → executed, placed at (2,2,EAST)
  Turn 1: A → MOVE 5          → executed, advanced 2 cells (blocked at east edge), moved to (4,2,EAST)
  Turn 2: A → REPORT          → executed, output "4,2,EAST"
```

### Example 6: Two robots, no collision

```
Board: 5x5, no obstacles
Robots: [A, B]

Commands (stacks are parallel — each column is one turn):
  A: PLACE 0,0,NORTH    B: PLACE 4,4,SOUTH
  A: MOVE                B: MOVE
  A: REPORT              B: REPORT

Snapshots:
  Turn 0: A → PLACE 0,0,NORTH → executed. B → PLACE 4,4,SOUTH → executed.
  Turn 1: A → MOVE → executed, (0,1,NORTH). B → MOVE → executed, (4,3,SOUTH).
  Turn 2: A → REPORT → "0,1,NORTH". B → REPORT → "4,3,SOUTH".
```

### Example 7: Two robots, collision blocking

```
Board: 5x5, no obstacles
Robots: [A, B]

Commands:
  A: PLACE 2,2,EAST      B: PLACE 3,2,WEST
  A: MOVE                 B: MOVE

Snapshots:
  Turn 0: A → PLACE 2,2,EAST → executed. B → PLACE 3,2,WEST → executed.
  Turn 1: A → MOVE → blocked, reason: "collision with robot B at (3,2)", stays at (2,2,EAST).
           B → MOVE → blocked, reason: "collision with robot A at (2,2)", stays at (3,2,WEST).
```

### Example 8: Obstacle blocking

```
Board: 5x5, obstacles: {"wall": [[2,1], [2,2], [2,3]]}
Robots: [A]

Commands:
  A: PLACE 0,2,EAST
  A: MOVE 5
  A: REPORT

Snapshots:
  Turn 0: A → PLACE 0,2,EAST → executed, placed at (0,2,EAST)
  Turn 1: A → MOVE 5          → executed, advanced 1 cell (blocked by obstacle "wall" at (2,2)), moved to (1,2,EAST)
  Turn 2: A → REPORT          → executed, output "1,2,EAST"
```

### Example 9: PLACE to occupied cell is ignored

```
Board: 5x5, no obstacles
Robots: [A, B]

Commands:
  A: PLACE 2,2,NORTH     B: PLACE 2,2,SOUTH
  A: REPORT               B: REPORT

Snapshots:
  Turn 0: A → PLACE 2,2,NORTH → executed.
           B → PLACE 2,2,SOUTH → blocked, reason: "cell (2,2) occupied by robot A". B not placed.
  Turn 1: A → REPORT → executed, output "2,2,NORTH".
           B → REPORT → blocked, reason: "robot not placed".
```

### Example 10: Resolution order — sequential resolution

```
Board: 5x5, no obstacles
Robots: [A, B]  (A added first, resolves first)

Commands:
  A: PLACE 1,0,NORTH     B: PLACE 2,0,NORTH
  A: MOVE                 B: PLACE 1,0,EAST

Snapshots:
  Turn 0: A → PLACE 1,0,NORTH → executed. B → PLACE 2,0,NORTH → executed.
  Turn 1: A → MOVE → executed, moved to (1,1,NORTH).
           B → PLACE 1,0,EAST → executed, placed at (1,0,EAST). Cell (1,0) was vacated by A earlier this turn.
```

### Example 11: LEFT N and RIGHT N

```
Board: 5x5, no obstacles
Robots: [A]

Commands:
  A: PLACE 0,0,NORTH
  A: LEFT 3
  A: REPORT

Snapshots:
  Turn 0: A → PLACE 0,0,NORTH → executed, placed at (0,0,NORTH)
  Turn 1: A → LEFT 3           → executed, rotated 270° CCW (= 90° CW), now facing EAST
  Turn 2: A → REPORT           → executed, output "0,0,EAST"
```

## Test Cases

Tests use `pytest`. Test the core directly by constructing `SimulationRequest` objects and calling `simulate()`. Each test asserts on the returned snapshots.

**Required test coverage:**

1. **Parsing**: valid commands (all types, with and without N), invalid commands (bad format, unknown words, negative numbers)
2. **Single robot basics**: PLACE + MOVE + REPORT (examples 1-3), all four directions
3. **Fall prevention**: MOVE at each edge (N/S/E/W), MOVE N that would overshoot
4. **Turning**: LEFT, RIGHT, LEFT N, RIGHT N, wrap-around (LEFT 4 = no change)
5. **MOVE N partial advance**: stops at edge, stops at obstacle, stops at robot
6. **Multi-robot no collision**: robots in separate areas (example 6)
7. **Multi-robot collision**: mutual blocking (example 7), PLACE to occupied cell (example 9)
8. **Obstacle blocking**: MOVE into obstacle, MOVE N stopped by obstacle (example 8), PLACE on obstacle cell
9. **Resolution order**: sequential resolution allows move-into-vacated-cell (example 10)
10. **Unplaced robot**: commands before PLACE are ignored, PLACE to invalid position leaves robot unplaced
11. **Null commands**: robot with null command does nothing, state preserved
12. **Re-PLACE**: robot can be re-PLACEd to a new valid position mid-simulation
