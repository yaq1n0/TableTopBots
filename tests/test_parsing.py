import pytest

from core.models import Direction
from core.parsing import is_valid_command, parse_command


class TestParseCommand:
    @pytest.mark.parametrize(
        "input_str,expected_type,expected_attrs",
        [
            ("PLACE 2,3,NORTH", "PLACE", {"x": 2, "y": 3, "facing": Direction.NORTH}),
            ("place 1,2,east", "PLACE", {"x": 1, "y": 2, "facing": Direction.EAST}),
            ("MOVE", "MOVE", {"count": 1}),
            ("MOVE 5", "MOVE", {"count": 5}),
            ("LEFT", "LEFT", {"count": 1}),
            ("LEFT 3", "LEFT", {"count": 3}),
            ("RIGHT", "RIGHT", {"count": 1}),
            ("RIGHT 2", "RIGHT", {"count": 2}),
            ("REPORT", "REPORT", {}),
        ],
    )
    def test_valid(self, input_str, expected_type, expected_attrs):
        cmd = parse_command(input_str)
        assert cmd.type == expected_type
        for attr, expected_val in expected_attrs.items():
            assert getattr(cmd, attr) == expected_val

    @pytest.mark.parametrize(
        "input_str",
        [
            "JUMP",
            "PLACE 1,2",
            "",
            "MOVE -1",
            "PLACE 1,2,UP",
        ],
    )
    def test_invalid(self, input_str):
        with pytest.raises(ValueError):
            parse_command(input_str)


class TestIsValidCommand:
    @pytest.mark.parametrize(
        "input_str,expected",
        [
            ("PLACE 0,0,NORTH", True),
            ("MOVE", True),
            ("MOVE 3", True),
            ("LEFT", True),
            ("LEFT 2", True),
            ("RIGHT", True),
            ("RIGHT 4", True),
            ("REPORT", True),
            ("", False),
            ("JUMP", False),
            ("PLACE 1,2", False),
            ("MOVE -1", False),
            ("PLACE 1,2,UP", False),
        ],
    )
    def test_is_valid_command(self, input_str, expected):
        assert is_valid_command(input_str) is expected
