from __future__ import annotations

from core.models import (
    Board,
    CommandResult,
    Direction,
    LeftCommand,
    MoveCommand,
    PlaceCommand,
    ReportCommand,
    RightCommand,
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
    """
    Rotate a facing by the given number of 90-degree steps
    (positive=right, negative=left).
    """
    idx = _DIRECTION_ORDER.index(facing)
    return _DIRECTION_ORDER[(idx + steps) % 4]


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------


class Engine:
    """
    Simulation engine that manages board state and robot positions.

    Can run a full batch simulation via simulate(), or be used
    interactively by calling submit_command() per robot per turn.
    """

    def __init__(
        self,
        width: int = 5,
        height: int = 5,
        obstacles: dict[str, list[tuple[int, int]]] | None = None,
    ) -> None:
        self.board = Board(
            width=width,
            height=height,
            obstacle_map=self._build_obstacle_map(obstacles or {}),
        )
        self.robots: dict[str, RobotState] = {}
        self.snapshots: list[Snapshot] = []
        self._turn: int = 0

    @classmethod
    def from_request(cls, request: SimulationRequest) -> Engine:
        engine = cls(
            width=request.width,
            height=request.height,
            obstacles=request.obstacles,
        )
        for name in request.robots:
            engine.add_robot(name)
        return engine

    # -- public API ------------------------------------------------------------

    def add_robot(self, name: str) -> None:
        self.robots[name] = RobotState(name=name)

    def submit_command(self, robot_name: str, cmd_str: str | None) -> CommandResult:
        """Submit a single command for a robot and resolve it immediately."""
        robot = self.robots[robot_name]
        return self._resolve_robot_turn(robot, cmd_str)

    def snapshot(self, turn: int | None = None) -> Snapshot:
        """Capture the current state of all robots as a Snapshot."""
        t = turn if turn is not None else self._turn
        return Snapshot(
            turn=t,
            robots=[r.model_copy() for r in self.robots.values()],
            results=[],
        )

    def simulate(
        self, command_stacks: dict[str, list[str | None]]
    ) -> SimulationResponse:
        """Run a full batch simulation from command stacks."""
        num_turns = max((len(stack) for stack in command_stacks.values()), default=0)
        robot_list = list(self.robots.values())

        snapshots: list[Snapshot] = []
        for turn in range(num_turns):
            results: list[CommandResult] = []
            for robot in robot_list:
                stack = command_stacks[robot.name]
                cmd_str = stack[turn] if turn < len(stack) else None
                result = self._resolve_robot_turn(robot, cmd_str)
                results.append(result)
            snapshots.append(
                Snapshot(
                    turn=turn,
                    robots=[r.model_copy() for r in robot_list],
                    results=results,
                )
            )

        return SimulationResponse(snapshots=snapshots)

    # -- internal helpers ------------------------------------------------------

    @staticmethod
    def _build_obstacle_map(
        obstacles: dict[str, list[tuple[int, int]]],
    ) -> dict[tuple[int, int], str]:
        return {
            (pos[0], pos[1]): name
            for name, positions in obstacles.items()
            for pos in positions
        }

    def _rejection_reason(self, x: int, y: int, moving_robot_name: str) -> str | None:
        if not (0 <= x < self.board.width and 0 <= y < self.board.height):
            return f"position ({x},{y}) is out of bounds"

        pos = (x, y)
        if pos in self.board.obstacle_map:
            return f'blocked by obstacle "{self.board.obstacle_map[pos]}" at ({x},{y})'

        if pos in self.board.occupied and self.board.occupied[pos] != moving_robot_name:
            return f"collision with robot {self.board.occupied[pos]} at ({x},{y})"

        return None

    def _resolve_robot_turn(
        self, robot: RobotState, cmd_str: str | None
    ) -> CommandResult:
        if cmd_str is None:
            return CommandResult(
                robot_name=robot.name, command=None, executed=False, reason="no command"
            )

        cmd = parse_command(cmd_str)

        if not robot.placed and not isinstance(cmd, PlaceCommand):
            return CommandResult(
                robot_name=robot.name,
                command=cmd,
                executed=False,
                reason="robot not placed",
            )

        return self._resolve_command(robot, cmd)

    def _resolve_command(
        self,
        robot: RobotState,
        cmd: PlaceCommand | MoveCommand | LeftCommand | RightCommand | ReportCommand,
    ) -> CommandResult:
        if isinstance(cmd, PlaceCommand):
            return self._resolve_place(robot, cmd)
        if isinstance(cmd, MoveCommand):
            return self._resolve_move(robot, cmd)
        if isinstance(cmd, LeftCommand):
            return self._resolve_left(robot, cmd)
        if isinstance(cmd, RightCommand):
            return self._resolve_right(robot, cmd)
        return self._resolve_report(robot, cmd)

    def _resolve_place(self, robot: RobotState, cmd: PlaceCommand) -> CommandResult:
        x, y = cmd.x, cmd.y

        reason = self._rejection_reason(x, y, robot.name)
        if reason is not None:
            pos = (x, y)
            if pos in self.board.obstacle_map:
                obs = self.board.obstacle_map[pos]
                reason = f'cell ({x},{y}) occupied by obstacle "{obs}"'
            elif pos in self.board.occupied:
                reason = f"cell ({x},{y}) occupied by robot {self.board.occupied[pos]}"
            return CommandResult(
                robot_name=robot.name, command=cmd, executed=False, reason=reason
            )

        old_pos = (robot.x, robot.y)
        if robot.placed and self.board.occupied.get(old_pos) == robot.name:
            del self.board.occupied[old_pos]

        robot.x = x
        robot.y = y
        robot.facing = cmd.facing
        robot.placed = True
        self.board.occupied[(x, y)] = robot.name

        return CommandResult(robot_name=robot.name, command=cmd, executed=True)

    def _resolve_move(self, robot: RobotState, cmd: MoveCommand) -> CommandResult:
        dx, dy = _DIRECTION_DELTA[robot.facing]
        steps_taken = 0

        for _ in range(cmd.count):
            nx, ny = robot.x + dx, robot.y + dy

            reason = self._rejection_reason(nx, ny, robot.name)
            if reason is not None:
                if steps_taken == 0:
                    if not (0 <= nx < self.board.width and 0 <= ny < self.board.height):
                        reason = f"would fall off {robot.facing.value.lower()} edge"
                    return CommandResult(
                        robot_name=robot.name,
                        command=cmd,
                        executed=False,
                        reason=reason,
                    )
                break

            old_pos = (robot.x, robot.y)
            if self.board.occupied.get(old_pos) == robot.name:
                del self.board.occupied[old_pos]

            robot.x = nx
            robot.y = ny
            self.board.occupied[(nx, ny)] = robot.name
            steps_taken += 1

        return CommandResult(
            robot_name=robot.name, command=cmd, executed=steps_taken > 0
        )

    def _resolve_left(self, robot: RobotState, cmd: LeftCommand) -> CommandResult:
        robot.facing = _rotate(robot.facing, -cmd.count)
        return CommandResult(robot_name=robot.name, command=cmd, executed=True)

    def _resolve_right(self, robot: RobotState, cmd: RightCommand) -> CommandResult:
        robot.facing = _rotate(robot.facing, cmd.count)
        return CommandResult(robot_name=robot.name, command=cmd, executed=True)

    def _resolve_report(self, robot: RobotState, cmd: ReportCommand) -> CommandResult:
        output = f"{robot.x},{robot.y},{robot.facing.value}"
        return CommandResult(
            robot_name=robot.name, command=cmd, executed=True, output=output
        )


# ---------------------------------------------------------------------------
# Public simulation entry point (backwards-compatible)
# ---------------------------------------------------------------------------


def simulate(request: SimulationRequest) -> SimulationResponse:
    """
    Public entry point for running a simulation.
    Creates an Engine instance and runs the batch simulation.
    """
    engine = Engine.from_request(request)
    return engine.simulate(request.robots)
