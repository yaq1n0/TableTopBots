from __future__ import annotations

from core.models import (
    Board,
    Command,
    CommandResult,
    Direction,
    RobotState,
    SimulationRequest,
    SimulationResponse,
    Snapshot,
)
from core.parsing import parse_command

_DIRECTION_ORDER = [Direction.NORTH, Direction.EAST, Direction.SOUTH, Direction.WEST]

_DIRECTION_DELTA: dict[Direction, tuple[int, int]] = {
    Direction.NORTH: (0, 1),
    Direction.SOUTH: (0, -1),
    Direction.EAST: (1, 0),
    Direction.WEST: (-1, 0),
}


# ---------------------------------------------------------------------------
# Direction helpers
# ---------------------------------------------------------------------------


def _rotate(facing: Direction, steps: int) -> Direction:
    idx = _DIRECTION_ORDER.index(facing)
    return _DIRECTION_ORDER[(idx + steps) % 4]


# ---------------------------------------------------------------------------
# Board helpers
# ---------------------------------------------------------------------------


def _build_obstacle_map(
    obstacles: dict[str, list[tuple[int, int]]],
) -> dict[tuple[int, int], str]:
    """Flatten {name: [positions]} into a cell -> obstacle-name lookup."""
    return {
        (pos[0], pos[1]): name
        for name, positions in obstacles.items()
        for pos in positions
    }


def _rejection_reason(
    x: int,
    y: int,
    board: Board,
    moving_robot_name: str,
) -> str | None:
    """Return a human-readable rejection reason if the cell is invalid, else None.

    Checks bounds, obstacles, and robot collisions in one pass.
    """
    if not (0 <= x < board.width and 0 <= y < board.height):
        return f"position ({x},{y}) is out of bounds"

    pos = (x, y)
    if pos in board.obstacle_map:
        return f'blocked by obstacle "{board.obstacle_map[pos]}" at ({x},{y})'

    if pos in board.occupied and board.occupied[pos] != moving_robot_name:
        return f"collision with robot {board.occupied[pos]} at ({x},{y})"

    return None


# ---------------------------------------------------------------------------
# Per-turn simulation helpers
# ---------------------------------------------------------------------------


def _process_turn(
    turn: int,
    robots: list[RobotState],
    request: SimulationRequest,
    board: Board,
) -> Snapshot:
    results: list[CommandResult] = []

    for i, robot in enumerate(robots):
        stack = request.command_stacks[i]
        cmd_str = stack[turn] if turn < len(stack) else None
        result = _resolve_robot_turn(robot, cmd_str, board)
        results.append(result)

    return Snapshot(turn=turn, robots=[r.model_copy() for r in robots], results=results)


def _resolve_robot_turn(
    robot: RobotState,
    cmd_str: str | None,
    board: Board,
) -> CommandResult:
    if cmd_str is None:
        return CommandResult(
            robot_name=robot.name, command=None, executed=False, reason="no command"
        )

    cmd = parse_command(cmd_str)

    if not robot.placed and cmd.type != "PLACE":
        return CommandResult(
            robot_name=robot.name,
            command=cmd,
            executed=False,
            reason="robot not placed",
        )

    return _resolve_command(robot, cmd, board)


# ---------------------------------------------------------------------------
# Public simulation entry point
# ---------------------------------------------------------------------------


def simulate(request: SimulationRequest) -> SimulationResponse:
    board = Board(
        width=request.width,
        height=request.height,
        obstacle_map=_build_obstacle_map(request.obstacles),
    )
    robots: list[RobotState] = [RobotState(name=name) for name in request.robot_names]

    num_turns = max((len(stack) for stack in request.command_stacks), default=0)

    snapshots = [
        _process_turn(turn, robots, request, board) for turn in range(num_turns)
    ]

    return SimulationResponse(snapshots=snapshots)


# ---------------------------------------------------------------------------
# Command resolvers
# ---------------------------------------------------------------------------


def _resolve_command(
    robot: RobotState,
    cmd: Command,
    board: Board,
) -> CommandResult:
    if cmd.type == "PLACE":
        return _resolve_place(robot, cmd, board)
    if cmd.type == "MOVE":
        return _resolve_move(robot, cmd, board)
    if cmd.type == "LEFT":
        return _resolve_left(robot, cmd)
    if cmd.type == "RIGHT":
        return _resolve_right(robot, cmd)
    if cmd.type == "REPORT":
        return _resolve_report(robot, cmd)
    return CommandResult(
        robot_name=robot.name, command=cmd, executed=False, reason="unknown command"
    )


def _resolve_place(
    robot: RobotState,
    cmd: Command,
    board: Board,
) -> CommandResult:
    x, y = cmd.x, cmd.y
    if x is None or y is None or cmd.facing is None:
        return CommandResult(
            robot_name=robot.name,
            command=cmd,
            executed=False,
            reason="invalid PLACE arguments",
        )

    reason = _rejection_reason(x, y, board, robot.name)
    if reason is not None:
        pos = (x, y)
        if pos in board.obstacle_map:
            reason = f'cell ({x},{y}) occupied by obstacle "{board.obstacle_map[pos]}"'
        elif pos in board.occupied:
            reason = f"cell ({x},{y}) occupied by robot {board.occupied[pos]}"
        return CommandResult(
            robot_name=robot.name, command=cmd, executed=False, reason=reason
        )

    old_pos = (robot.x, robot.y)
    if robot.placed and board.occupied.get(old_pos) == robot.name:
        del board.occupied[old_pos]

    robot.x = x
    robot.y = y
    robot.facing = cmd.facing
    robot.placed = True
    board.occupied[(x, y)] = robot.name

    return CommandResult(robot_name=robot.name, command=cmd, executed=True)


def _resolve_move(
    robot: RobotState,
    cmd: Command,
    board: Board,
) -> CommandResult:
    dx, dy = _DIRECTION_DELTA[robot.facing]
    steps_taken = 0

    for _ in range(cmd.count):
        nx, ny = robot.x + dx, robot.y + dy

        reason = _rejection_reason(nx, ny, board, robot.name)
        if reason is not None:
            if steps_taken == 0:
                # Provide edge-specific message for out-of-bounds
                if not (0 <= nx < board.width and 0 <= ny < board.height):
                    reason = f"would fall off {robot.facing.value.lower()} edge"
                return CommandResult(
                    robot_name=robot.name, command=cmd, executed=False, reason=reason
                )
            break

        old_pos = (robot.x, robot.y)
        if board.occupied.get(old_pos) == robot.name:
            del board.occupied[old_pos]

        robot.x = nx
        robot.y = ny
        board.occupied[(nx, ny)] = robot.name
        steps_taken += 1

    return CommandResult(robot_name=robot.name, command=cmd, executed=steps_taken > 0)


def _resolve_left(robot: RobotState, cmd: Command) -> CommandResult:
    robot.facing = _rotate(robot.facing, -cmd.count)
    return CommandResult(robot_name=robot.name, command=cmd, executed=True)


def _resolve_right(robot: RobotState, cmd: Command) -> CommandResult:
    robot.facing = _rotate(robot.facing, cmd.count)
    return CommandResult(robot_name=robot.name, command=cmd, executed=True)


def _resolve_report(robot: RobotState, cmd: Command) -> CommandResult:
    output = f"{robot.x},{robot.y},{robot.facing.value}"
    return CommandResult(
        robot_name=robot.name, command=cmd, executed=True, output=output
    )
