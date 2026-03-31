from __future__ import annotations

import re

from core.models import (
    Direction,
    LeftCommand,
    MoveCommand,
    PlaceCommand,
    ReportCommand,
    RightCommand,
)

_PLACE_RE = re.compile(
    r"^PLACE\s+(\d+)\s*,\s*(\d+)\s*,\s*(NORTH|SOUTH|EAST|WEST)$", re.IGNORECASE
)
_MOVE_RE = re.compile(r"^MOVE(?:\s+(\d+))?$", re.IGNORECASE)
_LEFT_RE = re.compile(r"^LEFT(?:\s+(\d+))?$", re.IGNORECASE)
_RIGHT_RE = re.compile(r"^RIGHT(?:\s+(\d+))?$", re.IGNORECASE)
_REPORT_RE = re.compile(r"^REPORT$", re.IGNORECASE)


def parse_command(
    s: str,
) -> PlaceCommand | MoveCommand | LeftCommand | RightCommand | ReportCommand:
    s = s.strip()

    m = _PLACE_RE.match(s)
    if m:
        return PlaceCommand(
            x=int(m.group(1)),
            y=int(m.group(2)),
            facing=Direction(m.group(3).upper()),
        )

    m = _MOVE_RE.match(s)
    if m:
        count = int(m.group(1)) if m.group(1) else 1
        return MoveCommand(count=count)

    m = _LEFT_RE.match(s)
    if m:
        count = int(m.group(1)) if m.group(1) else 1
        return LeftCommand(count=count)

    m = _RIGHT_RE.match(s)
    if m:
        count = int(m.group(1)) if m.group(1) else 1
        return RightCommand(count=count)

    m = _REPORT_RE.match(s)
    if m:
        return ReportCommand()

    raise ValueError(f"Invalid command: {s}")


def is_valid_command(command_str: str) -> bool:
    try:
        parse_command(command_str)
        return True
    except ValueError:
        return False
