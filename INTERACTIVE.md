# Interactive Mode — Implementation Plan

## Overview

Add a third UI phase (`interactive`) alongside the existing `setup` and `run` phases. In interactive mode, the user controls a single robot in real-time — either by typing commands into an input or using WASD keyboard controls. The board updates live after each command.

---

## 1. Backend: Engine & API

### 1.1 Engine (already refactored)

The `Engine` class now holds board state as instance fields and exposes `submit_command(robot_name, cmd_str)` for single-command resolution. This is the foundation for interactive mode — no batch simulation needed.

### 1.2 New API: WebSocket endpoint

Add a WebSocket endpoint to `api/main.py` for stateful, low-latency interactive sessions.

```
WS /interactive
```

**Session lifecycle:**

1. Client sends `init` message with board config (width, height, obstacles) and robot name
2. Server creates an `Engine` instance, adds the robot, auto-places it at a default position (or client specifies)
3. Client sends command messages (`{"command": "MOVE"}`, `{"command": "LEFT"}`, etc.)
4. Server calls `engine.submit_command()`, responds with `CommandResult` + current `RobotState`
5. Client sends `disconnect` or WebSocket closes — server discards the engine

**Message format:**

```jsonc
// Client → Server
{"type": "init", "width": 5, "height": 5, "obstacles": {}, "robot": "Player", "x": 0, "y": 0, "facing": "NORTH"}
{"type": "command", "command": "MOVE"}
{"type": "command", "command": "LEFT"}

// Server → Client
{"type": "state", "robot": {RobotState}, "result": {CommandResult}}
{"type": "error", "message": "..."}
```

**Why WebSocket over REST:** Interactive mode sends rapid, sequential commands against persistent engine state. A WebSocket avoids re-creating the engine per request and eliminates HTTP overhead for what is essentially a stateful session.

### 1.3 Alternative: REST with session ID

If WebSocket adds too much complexity initially, a simpler option:

- `POST /interactive/start` → returns `session_id`, creates engine server-side (stored in a dict keyed by session ID)
- `POST /interactive/{session_id}/command` → submit command, returns result + state
- `DELETE /interactive/{session_id}` → cleanup
- Add a TTL/cleanup for stale sessions

This is simpler to implement but less responsive for WASD controls.

---

## 2. Frontend: UI Changes

### 2.1 New phase: `interactive`

Extend `Phase` type in `App.tsx`:

```ts
type Phase = 'setup' | 'run' | 'interactive'
```

Add an "Interactive" button alongside the existing "Simulate" button in the setup header. Clicking it transitions to `interactive` phase with a single robot.

### 2.2 New hook: `useInteractive`

`ui/src/hooks/useInteractive.ts`

Manages:
- WebSocket connection to `/interactive`
- Current `RobotState` (updated after each command)
- Command history (list of `CommandResult` for the sidebar log)
- `sendCommand(cmd: string)` function
- Connection status

### 2.3 WASD keyboard controls

Handle in `useInteractive` via a `keydown` event listener.

**WASD mapping logic (single-robot, direction-aware):**

| Key | Robot facing that direction? | Action |
|-----|---------------------------|--------|
| W   | Facing NORTH              | MOVE   |
| W   | Not facing NORTH          | LEFT/RIGHT to face NORTH |
| A   | Facing WEST               | MOVE   |
| A   | Not facing WEST           | LEFT/RIGHT to face WEST  |
| S   | Facing SOUTH              | MOVE   |
| S   | Not facing SOUTH          | LEFT/RIGHT to face SOUTH |
| D   | Facing EAST               | MOVE   |
| D   | Not facing EAST           | LEFT/RIGHT to face EAST  |

The rotation direction (LEFT vs RIGHT) should pick the shortest turn. For example, if facing NORTH and pressing D (EAST), send RIGHT. If facing NORTH and pressing A (WEST), send LEFT.

This means a single keypress either rotates or moves — never both. To move in a new direction, press the key twice: once to rotate, once to move. This keeps it predictable and matches the engine's one-command-at-a-time model.

**Debounce/throttle:** Add a small cooldown (~100ms) to prevent command spam from key repeat.

### 2.4 Command input

Below the board, add a text input for typing raw commands (PLACE, MOVE, LEFT, RIGHT, REPORT). This uses the same `sendCommand` from `useInteractive`, giving power users direct control while WASD handles casual movement.

### 2.5 Interactive sidebar

Replace the setup/run sidebar content with:
- Current robot state (position, facing) — always visible at top
- Scrollable command log showing each command and its result (success/failure + reason)
- A "Reset" button that re-initializes the engine to starting state

### 2.6 BoardGrid updates

`BoardGrid` already accepts `robots` as a prop and renders them. In interactive mode, pass `[currentRobotState]` as the robots array. No changes needed to the grid component itself — it's already reactive.

---

## 3. File changes summary

| File | Change |
|------|--------|
| `core/engine.py` | Done — class refactor with `submit_command()` |
| `api/main.py` | Add WebSocket `/interactive` endpoint |
| `ui/src/App.tsx` | Add `interactive` phase, wire up new hook + UI |
| `ui/src/hooks/useInteractive.ts` | New — WebSocket, WASD, command dispatch |
| `ui/src/components/InteractiveSidebar.tsx` | New — robot state display + command log |
| `ui/src/components/CommandInput.tsx` | New — text input for manual commands |
| `ui/src/api.ts` | Add WebSocket connection helper |
| `ui/src/types.ts` | Extend types if needed for interactive state |
| `ui/package.json` | No new deps needed (browser WebSocket API is native) |

---

## 4. Implementation order

1. **Backend WebSocket endpoint** — get the server side working first, testable via `wscat`
2. **`useInteractive` hook** — WebSocket connection + `sendCommand`
3. **Wire into App.tsx** — new phase, button, basic rendering
4. **Command input** — type commands manually, verify round-trip works
5. **WASD controls** — add keyboard handler with rotation logic
6. **Interactive sidebar** — command log, robot state display
7. **Polish** — connection status indicator, error handling, reconnection

---

## 5. Future extensions

- **Multi-robot interactive:** Each connected WebSocket client controls one robot on a shared board
- **Replay in interactive:** Record commands during interactive session, replay as a batch simulation
- **Mobile controls:** On-screen directional buttons for touch devices
- **Undo:** Engine could maintain a state history stack for stepping backwards
