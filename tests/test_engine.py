import pytest

from core.engine import simulate
from core.models import (
    Command,
    CommandResult,
    Direction,
    RobotState,
    SimulationRequest,
    Snapshot,
)


def _sim(robot_names, command_stacks, width=5, height=5, obstacles=None):
    req = SimulationRequest(
        width=width,
        height=height,
        obstacles=obstacles or {},
        robot_names=robot_names,
        command_stacks=command_stacks,
    )
    return simulate(req)


def _robot(name, x, y, facing, placed=True) -> RobotState:
    return RobotState(name=name, x=x, y=y, facing=facing, placed=placed)


def _result(robot_name, cmd, executed, reason=None, output=None) -> CommandResult:
    return CommandResult(
        robot_name=robot_name,
        command=cmd,
        executed=executed,
        reason=reason,
        output=output,
    )


def _place_cmd(x, y, facing) -> Command:
    return Command(type="PLACE", x=x, y=y, facing=Direction(facing))


def _move_cmd(count=1) -> Command:
    return Command(type="MOVE", count=count)


def _left_cmd(count=1) -> Command:
    return Command(type="LEFT", count=count)


def _right_cmd(count=1) -> Command:
    return Command(type="RIGHT", count=count)


def _report_cmd() -> Command:
    return Command(type="REPORT")


class TestSingleRobotBasics:
    """Examples 1-3 from spec."""

    def test_example1_basic_movement(self):
        res = _sim(["A"], [["PLACE 0,0,NORTH", "MOVE", "REPORT"]])
        assert res.snapshots == [
            Snapshot(
                turn=0,
                robots=[_robot("A", 0, 0, Direction.NORTH)],
                results=[_result("A", _place_cmd(0, 0, "NORTH"), executed=True)],
            ),
            Snapshot(
                turn=1,
                robots=[_robot("A", 0, 1, Direction.NORTH)],
                results=[_result("A", _move_cmd(), executed=True)],
            ),
            Snapshot(
                turn=2,
                robots=[_robot("A", 0, 1, Direction.NORTH)],
                results=[
                    _result("A", _report_cmd(), executed=True, output="0,1,NORTH")
                ],
            ),
        ]

    def test_example2_turning(self):
        res = _sim(["A"], [["PLACE 0,0,NORTH", "LEFT", "REPORT"]])
        assert res.snapshots == [
            Snapshot(
                turn=0,
                robots=[_robot("A", 0, 0, Direction.NORTH)],
                results=[_result("A", _place_cmd(0, 0, "NORTH"), executed=True)],
            ),
            Snapshot(
                turn=1,
                robots=[_robot("A", 0, 0, Direction.WEST)],
                results=[_result("A", _left_cmd(), executed=True)],
            ),
            Snapshot(
                turn=2,
                robots=[_robot("A", 0, 0, Direction.WEST)],
                results=[_result("A", _report_cmd(), executed=True, output="0,0,WEST")],
            ),
        ]

    def test_example3_compound_movement(self):
        res = _sim(
            ["A"], [["PLACE 1,2,EAST", "MOVE", "MOVE", "LEFT", "MOVE", "REPORT"]]
        )
        assert res.snapshots[5] == Snapshot(
            turn=5,
            robots=[_robot("A", 3, 3, Direction.NORTH)],
            results=[_result("A", _report_cmd(), executed=True, output="3,3,NORTH")],
        )

    @pytest.mark.parametrize(
        "direction,dx,dy",
        [("NORTH", 0, 1), ("SOUTH", 0, -1), ("EAST", 1, 0), ("WEST", -1, 0)],
    )
    def test_all_directions(self, direction, dx, dy):
        res = _sim(["A"], [[f"PLACE 2,2,{direction}", "MOVE", "REPORT"]])
        assert res.snapshots[2] == Snapshot(
            turn=2,
            robots=[_robot("A", 2 + dx, 2 + dy, Direction(direction))],
            results=[
                _result(
                    "A",
                    _report_cmd(),
                    executed=True,
                    output=f"{2 + dx},{2 + dy},{direction}",
                )
            ],
        )


class TestFallPrevention:
    """Example 4 from spec."""

    def test_example4_north_edge(self):
        res = _sim(["A"], [["PLACE 4,4,NORTH", "MOVE", "REPORT"]])
        assert res.snapshots[1] == Snapshot(
            turn=1,
            robots=[_robot("A", 4, 4, Direction.NORTH)],
            results=[
                _result(
                    "A", _move_cmd(), executed=False, reason="would fall off north edge"
                )
            ],
        )
        assert res.snapshots[2].results[0].output == "4,4,NORTH"

    @pytest.mark.parametrize(
        "x,y,direction",
        [(0, 0, "SOUTH"), (4, 2, "EAST"), (0, 2, "WEST")],
    )
    def test_edge_blocked(self, x, y, direction):
        res = _sim(["A"], [[f"PLACE {x},{y},{direction}", "MOVE"]])
        result = res.snapshots[1].results[0]
        assert result.executed is False
        assert "fall off" in result.reason
        assert res.snapshots[1].robots[0].x == x
        assert res.snapshots[1].robots[0].y == y


class TestTurning:
    def test_right(self):
        res = _sim(["A"], [["PLACE 0,0,NORTH", "RIGHT", "REPORT"]])
        assert res.snapshots[1] == Snapshot(
            turn=1,
            robots=[_robot("A", 0, 0, Direction.EAST)],
            results=[_result("A", _right_cmd(), executed=True)],
        )
        assert res.snapshots[2].results[0].output == "0,0,EAST"

    def test_left_n(self):
        # LEFT 3 from NORTH = EAST (270 CCW = 90 CW)
        res = _sim(["A"], [["PLACE 0,0,NORTH", "LEFT 3", "REPORT"]])
        assert res.snapshots[1] == Snapshot(
            turn=1,
            robots=[_robot("A", 0, 0, Direction.EAST)],
            results=[_result("A", _left_cmd(3), executed=True)],
        )
        assert res.snapshots[2].results[0].output == "0,0,EAST"

    def test_right_n(self):
        # RIGHT 2 from NORTH = SOUTH
        res = _sim(["A"], [["PLACE 0,0,NORTH", "RIGHT 2", "REPORT"]])
        assert res.snapshots[1].robots[0].facing == Direction.SOUTH
        assert res.snapshots[2].results[0].output == "0,0,SOUTH"

    def test_left_4_no_change(self):
        res = _sim(["A"], [["PLACE 0,0,NORTH", "LEFT 4", "REPORT"]])
        assert res.snapshots[1].robots[0].facing == Direction.NORTH
        assert res.snapshots[2].results[0].output == "0,0,NORTH"

    def test_right_4_no_change(self):
        res = _sim(["A"], [["PLACE 0,0,NORTH", "RIGHT 4", "REPORT"]])
        assert res.snapshots[1].robots[0].facing == Direction.NORTH
        assert res.snapshots[2].results[0].output == "0,0,NORTH"


class TestMoveN:
    """Example 5 from spec."""

    def test_example5_partial_advance_edge(self):
        res = _sim(["A"], [["PLACE 2,2,EAST", "MOVE 5", "REPORT"]])
        assert res.snapshots[1] == Snapshot(
            turn=1,
            robots=[_robot("A", 4, 2, Direction.EAST)],
            results=[_result("A", _move_cmd(5), executed=True)],
        )
        assert res.snapshots[2].results[0].output == "4,2,EAST"

    def test_move_n_stopped_by_obstacle(self):
        res = _sim(
            ["A"],
            [["PLACE 0,2,EAST", "MOVE 5", "REPORT"]],
            obstacles={"wall": [(2, 2)]},
        )
        assert res.snapshots[1] == Snapshot(
            turn=1,
            robots=[_robot("A", 1, 2, Direction.EAST)],
            results=[_result("A", _move_cmd(5), executed=True)],
        )
        assert res.snapshots[2].results[0].output == "1,2,EAST"

    def test_move_n_stopped_by_robot(self):
        res = _sim(
            ["A", "B"],
            [
                ["PLACE 0,0,EAST", "MOVE 5"],
                ["PLACE 3,0,NORTH", None],
            ],
        )
        assert res.snapshots[1] == Snapshot(
            turn=1,
            robots=[
                _robot("A", 2, 0, Direction.EAST),
                _robot("B", 3, 0, Direction.NORTH),
            ],
            results=[
                _result("A", _move_cmd(5), executed=True),
                _result("B", None, executed=False, reason="no command"),
            ],
        )

    def test_move_n_first_cell_blocked_by_edge(self):
        res = _sim(["A"], [["PLACE 4,4,NORTH", "MOVE 3"]])
        assert res.snapshots[1] == Snapshot(
            turn=1,
            robots=[_robot("A", 4, 4, Direction.NORTH)],
            results=[
                _result(
                    "A",
                    _move_cmd(3),
                    executed=False,
                    reason="would fall off north edge",
                )
            ],
        )

    def test_move_n_first_cell_blocked_by_obstacle(self):
        res = _sim(
            ["A"],
            [["PLACE 0,2,EAST", "MOVE 3"]],
            obstacles={"wall": [(1, 2)]},
        )
        assert res.snapshots[1] == Snapshot(
            turn=1,
            robots=[_robot("A", 0, 2, Direction.EAST)],
            results=[
                _result(
                    "A",
                    _move_cmd(3),
                    executed=False,
                    reason='blocked by obstacle "wall" at (1,2)',
                )
            ],
        )


class TestMultiRobotNoCollision:
    """Example 6 from spec."""

    def test_example6(self):
        res = _sim(
            ["A", "B"],
            [
                ["PLACE 0,0,NORTH", "MOVE", "REPORT"],
                ["PLACE 4,4,SOUTH", "MOVE", "REPORT"],
            ],
        )
        assert res.snapshots[2] == Snapshot(
            turn=2,
            robots=[
                _robot("A", 0, 1, Direction.NORTH),
                _robot("B", 4, 3, Direction.SOUTH),
            ],
            results=[
                _result("A", _report_cmd(), executed=True, output="0,1,NORTH"),
                _result("B", _report_cmd(), executed=True, output="4,3,SOUTH"),
            ],
        )


class TestMultiRobotCollision:
    """Examples 7 and 9 from spec."""

    def test_example7_mutual_blocking(self):
        res = _sim(
            ["A", "B"],
            [
                ["PLACE 2,2,EAST", "MOVE"],
                ["PLACE 3,2,WEST", "MOVE"],
            ],
        )
        assert res.snapshots[1] == Snapshot(
            turn=1,
            robots=[
                _robot("A", 2, 2, Direction.EAST),
                _robot("B", 3, 2, Direction.WEST),
            ],
            results=[
                _result(
                    "A",
                    _move_cmd(),
                    executed=False,
                    reason="collision with robot B at (3,2)",
                ),
                _result(
                    "B",
                    _move_cmd(),
                    executed=False,
                    reason="collision with robot A at (2,2)",
                ),
            ],
        )

    def test_example9_place_occupied(self):
        res = _sim(
            ["A", "B"],
            [
                ["PLACE 2,2,NORTH", "REPORT"],
                ["PLACE 2,2,SOUTH", "REPORT"],
            ],
        )
        assert res.snapshots[0] == Snapshot(
            turn=0,
            robots=[
                _robot("A", 2, 2, Direction.NORTH),
                _robot("B", 0, 0, Direction.NORTH, placed=False),
            ],
            results=[
                _result("A", _place_cmd(2, 2, "NORTH"), executed=True),
                _result(
                    "B",
                    _place_cmd(2, 2, "SOUTH"),
                    executed=False,
                    reason="cell (2,2) occupied by robot A",
                ),
            ],
        )
        # B not placed, so REPORT in turn 1 fails
        assert res.snapshots[1] == Snapshot(
            turn=1,
            robots=[
                _robot("A", 2, 2, Direction.NORTH),
                _robot("B", 0, 0, Direction.NORTH, placed=False),
            ],
            results=[
                _result("A", _report_cmd(), executed=True, output="2,2,NORTH"),
                _result("B", _report_cmd(), executed=False, reason="robot not placed"),
            ],
        )


class TestObstacleBlocking:
    """Example 8 from spec."""

    def test_example8(self):
        res = _sim(
            ["A"],
            [["PLACE 0,2,EAST", "MOVE 5", "REPORT"]],
            obstacles={"wall": [(2, 1), (2, 2), (2, 3)]},
        )
        assert res.snapshots[1] == Snapshot(
            turn=1,
            robots=[_robot("A", 1, 2, Direction.EAST)],
            results=[_result("A", _move_cmd(5), executed=True)],
        )
        assert res.snapshots[2].results[0].output == "1,2,EAST"

    def test_move_into_obstacle(self):
        res = _sim(["A"], [["PLACE 1,2,EAST", "MOVE"]], obstacles={"wall": [(2, 2)]})
        assert res.snapshots[1] == Snapshot(
            turn=1,
            robots=[_robot("A", 1, 2, Direction.EAST)],
            results=[
                _result(
                    "A",
                    _move_cmd(),
                    executed=False,
                    reason='blocked by obstacle "wall" at (2,2)',
                )
            ],
        )

    def test_place_on_obstacle(self):
        res = _sim(["A"], [["PLACE 2,2,NORTH"]], obstacles={"rock": [(2, 2)]})
        assert res.snapshots[0] == Snapshot(
            turn=0,
            robots=[_robot("A", 0, 0, Direction.NORTH, placed=False)],
            results=[
                _result(
                    "A",
                    _place_cmd(2, 2, "NORTH"),
                    executed=False,
                    reason='cell (2,2) occupied by obstacle "rock"',
                )
            ],
        )


class TestResolutionOrder:
    """Example 10 from spec."""

    def test_example10_sequential_resolution(self):
        res = _sim(
            ["A", "B"],
            [
                ["PLACE 1,0,NORTH", "MOVE"],
                ["PLACE 2,0,NORTH", "PLACE 1,0,EAST"],
            ],
        )
        # Turn 1: A moves to (1,1), then B places at (1,0) which is now empty
        assert res.snapshots[1] == Snapshot(
            turn=1,
            robots=[
                _robot("A", 1, 1, Direction.NORTH),
                _robot("B", 1, 0, Direction.EAST),
            ],
            results=[
                _result("A", _move_cmd(), executed=True),
                _result("B", _place_cmd(1, 0, "EAST"), executed=True),
            ],
        )


class TestUnplacedRobot:
    def test_commands_before_place_ignored(self):
        res = _sim(["A"], [["MOVE", "PLACE 0,0,NORTH", "REPORT"]])
        assert res.snapshots[0] == Snapshot(
            turn=0,
            robots=[_robot("A", 0, 0, Direction.NORTH, placed=False)],
            results=[
                _result("A", _move_cmd(), executed=False, reason="robot not placed")
            ],
        )
        assert res.snapshots[2].results[0].output == "0,0,NORTH"

    def test_place_to_invalid_position(self):
        res = _sim(["A"], [["PLACE 10,10,NORTH", "REPORT"]])
        assert res.snapshots[0] == Snapshot(
            turn=0,
            robots=[_robot("A", 0, 0, Direction.NORTH, placed=False)],
            results=[
                _result(
                    "A",
                    _place_cmd(10, 10, "NORTH"),
                    executed=False,
                    reason="position (10,10) is out of bounds",
                )
            ],
        )
        assert res.snapshots[1] == Snapshot(
            turn=1,
            robots=[_robot("A", 0, 0, Direction.NORTH, placed=False)],
            results=[
                _result("A", _report_cmd(), executed=False, reason="robot not placed")
            ],
        )


class TestNullCommands:
    def test_null_command(self):
        res = _sim(["A"], [["PLACE 0,0,NORTH", None, "REPORT"]])
        assert res.snapshots[1] == Snapshot(
            turn=1,
            robots=[_robot("A", 0, 0, Direction.NORTH)],
            results=[_result("A", None, executed=False, reason="no command")],
        )
        assert res.snapshots[2].results[0].output == "0,0,NORTH"


class TestRePlace:
    def test_re_place(self):
        res = _sim(["A"], [["PLACE 0,0,NORTH", "PLACE 3,3,SOUTH", "REPORT"]])
        assert res.snapshots[1] == Snapshot(
            turn=1,
            robots=[_robot("A", 3, 3, Direction.SOUTH)],
            results=[_result("A", _place_cmd(3, 3, "SOUTH"), executed=True)],
        )
        assert res.snapshots[2].results[0].output == "3,3,SOUTH"

    def test_re_place_frees_old_cell(self):
        """After A re-places, B can occupy A's old cell."""
        res = _sim(
            ["A", "B"],
            [
                ["PLACE 0,0,NORTH", "PLACE 3,3,SOUTH"],
                ["PLACE 1,1,EAST", "PLACE 0,0,EAST"],
            ],
        )
        assert res.snapshots[1].results[1].executed is True
        assert res.snapshots[1].robots[1].x == 0
        assert res.snapshots[1].robots[1].y == 0


class TestEdgeCases:
    def test_minimum_board_5x5(self):
        """5x5 is valid (minimum board size)."""
        res = _sim(["A"], [["PLACE 0,0,NORTH"]], width=5, height=5)
        assert res.snapshots[0].results[0].executed is True

    def test_board_smaller_than_minimum_rejected(self):
        """Boards smaller than 5x5 are rejected at model validation."""
        with pytest.raises(Exception):
            SimulationRequest(width=4, height=5, robot_names=[], command_stacks=[])
        with pytest.raises(Exception):
            SimulationRequest(width=5, height=4, robot_names=[], command_stacks=[])

    def test_place_on_corner_cells(self):
        """All four corners of a 5x5 board should be valid PLACE targets."""
        for x, y in [(0, 0), (4, 0), (0, 4), (4, 4)]:
            res = _sim(["A"], [[f"PLACE {x},{y},NORTH"]])
            assert res.snapshots[0].results[0].executed is True, (
                f"Corner ({x},{y}) should be placeable"
            )

    def test_place_just_outside_board(self):
        """Coordinates exactly at width/height are out of bounds."""
        res = _sim(["A"], [["PLACE 5,0,NORTH"]])
        assert res.snapshots[0].results[0].executed is False
        assert "out of bounds" in res.snapshots[0].results[0].reason

        res = _sim(["A"], [["PLACE 0,5,NORTH"]])
        assert res.snapshots[0].results[0].executed is False
        assert "out of bounds" in res.snapshots[0].results[0].reason

    def test_move_zero_count(self):
        """MOVE 0 is parsed but results in no movement; executed=False (no steps taken)."""
        res = _sim(["A"], [["PLACE 2,2,NORTH", "MOVE 0", "REPORT"]])
        assert res.snapshots[1].results[0].executed is False
        assert res.snapshots[2].results[0].output == "2,2,NORTH"

    def test_left_zero_count(self):
        """LEFT 0 rotates 0 steps; facing unchanged; executed=True."""
        res = _sim(["A"], [["PLACE 0,0,NORTH", "LEFT 0", "REPORT"]])
        assert res.snapshots[1].results[0].executed is True
        assert res.snapshots[2].results[0].output == "0,0,NORTH"

    def test_right_zero_count(self):
        """RIGHT 0 rotates 0 steps; facing unchanged; executed=True."""
        res = _sim(["A"], [["PLACE 0,0,NORTH", "RIGHT 0", "REPORT"]])
        assert res.snapshots[1].results[0].executed is True
        assert res.snapshots[2].results[0].output == "0,0,NORTH"

    def test_no_robots_no_commands(self):
        """Empty simulation produces zero snapshots."""
        res = _sim([], [])
        assert res.snapshots == []

    def test_recovery_after_failed_place(self):
        """A valid PLACE after a failed out-of-bounds PLACE should succeed."""
        res = _sim(["A"], [["PLACE 99,99,NORTH", "PLACE 2,2,EAST", "REPORT"]])
        assert res.snapshots[0].results[0].executed is False
        assert res.snapshots[1].results[0].executed is True
        assert res.snapshots[2].results[0].output == "2,2,EAST"

    def test_out_of_bounds_reason_message(self):
        """Out-of-bounds PLACE reports coordinates in the reason."""
        res = _sim(["A"], [["PLACE 7,3,NORTH"]])
        reason = res.snapshots[0].results[0].reason
        assert reason == "position (7,3) is out of bounds"

    def test_obstacle_covers_entire_row(self):
        """A wall spanning the full row blocks all movement east from (0,2)."""
        res = _sim(
            ["A"],
            [["PLACE 0,2,EAST", "MOVE 10"]],
            obstacles={"wall": [(x, 2) for x in range(1, 5)]},
        )
        assert res.snapshots[1] == Snapshot(
            turn=1,
            robots=[_robot("A", 0, 2, Direction.EAST)],
            results=[
                _result(
                    "A",
                    _move_cmd(10),
                    executed=False,
                    reason='blocked by obstacle "wall" at (1,2)',
                )
            ],
        )
