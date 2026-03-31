import pytest

from core.models import Direction
from core.parsing import is_valid_command, parse_command


class TestParseCommand:
    def test_place(self):
        cmd = parse_command("PLACE 2,3,NORTH")
        assert cmd.type == "PLACE"
        assert cmd.x == 2
        assert cmd.y == 3
        assert cmd.facing == Direction.NORTH

    def test_place_case_insensitive(self):
        cmd = parse_command("place 1,2,east")
        assert cmd.type == "PLACE"
        assert cmd.x == 1
        assert cmd.y == 2
        assert cmd.facing == Direction.EAST

    def test_move(self):
        cmd = parse_command("MOVE")
        assert cmd.type == "MOVE"
        assert cmd.count == 1

    def test_move_n(self):
        cmd = parse_command("MOVE 5")
        assert cmd.type == "MOVE"
        assert cmd.count == 5

    def test_left(self):
        cmd = parse_command("LEFT")
        assert cmd.type == "LEFT"
        assert cmd.count == 1

    def test_left_n(self):
        cmd = parse_command("LEFT 3")
        assert cmd.type == "LEFT"
        assert cmd.count == 3

    def test_right(self):
        cmd = parse_command("RIGHT")
        assert cmd.type == "RIGHT"
        assert cmd.count == 1

    def test_right_n(self):
        cmd = parse_command("RIGHT 2")
        assert cmd.type == "RIGHT"
        assert cmd.count == 2

    def test_report(self):
        cmd = parse_command("REPORT")
        assert cmd.type == "REPORT"

    def test_invalid_command(self):
        with pytest.raises(ValueError):
            parse_command("JUMP")

    def test_invalid_format(self):
        with pytest.raises(ValueError):
            parse_command("PLACE 1,2")

    def test_empty_string(self):
        with pytest.raises(ValueError):
            parse_command("")

    def test_negative_number(self):
        with pytest.raises(ValueError):
            parse_command("MOVE -1")

    def test_place_bad_direction(self):
        with pytest.raises(ValueError):
            parse_command("PLACE 1,2,UP")


class TestIsValidCommand:
    def test_valid_commands(self):
        assert is_valid_command("PLACE 0,0,NORTH") is True
        assert is_valid_command("MOVE") is True
        assert is_valid_command("MOVE 3") is True
        assert is_valid_command("LEFT") is True
        assert is_valid_command("LEFT 2") is True
        assert is_valid_command("RIGHT") is True
        assert is_valid_command("RIGHT 4") is True
        assert is_valid_command("REPORT") is True

    def test_invalid_commands(self):
        assert is_valid_command("") is False
        assert is_valid_command("JUMP") is False
        assert is_valid_command("PLACE 1,2") is False
        assert is_valid_command("MOVE -1") is False
        assert is_valid_command("PLACE 1,2,UP") is False
