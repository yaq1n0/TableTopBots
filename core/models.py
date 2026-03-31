from __future__ import annotations

from enum import StrEnum
from typing import Annotated, Literal

from pydantic import BaseModel, Field

BoardDim = Annotated[int, Field(ge=5, le=100)]


class Direction(StrEnum):
    NORTH = "NORTH"
    SOUTH = "SOUTH"
    EAST = "EAST"
    WEST = "WEST"


class PlaceCommand(BaseModel):
    type: Literal["PLACE"] = "PLACE"
    x: int
    y: int
    facing: Direction


class MoveCommand(BaseModel):
    type: Literal["MOVE"] = "MOVE"
    count: int = 1


class LeftCommand(BaseModel):
    type: Literal["LEFT"] = "LEFT"
    count: int = 1


class RightCommand(BaseModel):
    type: Literal["RIGHT"] = "RIGHT"
    count: int = 1


class ReportCommand(BaseModel):
    type: Literal["REPORT"] = "REPORT"


Command = Annotated[
    PlaceCommand | MoveCommand | LeftCommand | RightCommand | ReportCommand,
    Field(discriminator="type"),
]


class RobotState(BaseModel):
    name: str
    x: int = 0
    y: int = 0
    facing: Direction = Direction.NORTH
    placed: bool = False


class CommandResult(BaseModel):
    robot_name: str
    command: Command | None = None
    executed: bool
    reason: str | None = None
    output: str | None = None


class Snapshot(BaseModel):
    turn: int
    robots: list[RobotState]
    results: list[CommandResult]


class Board(BaseModel):
    width: BoardDim = 5
    height: BoardDim = 5
    obstacle_map: dict[tuple[int, int], str] = {}
    occupied: dict[tuple[int, int], str] = {}


class SimulationRequest(BaseModel):
    width: BoardDim = 5
    height: BoardDim = 5
    obstacles: dict[str, list[tuple[int, int]]] = {}
    robots: dict[str, list[str | None]] = {}


class SimulationResponse(BaseModel):
    snapshots: list[Snapshot]


class ValidateRequest(BaseModel):
    command: str


class ValidationResponse(BaseModel):
    valid: bool
    error: str | None = None


class ParseFileResponse(BaseModel):
    commands: list[str]


class ConfigRobot(BaseModel):
    name: str
    commands: list[str]


class ConfigFile(BaseModel):
    width: BoardDim = 5
    height: BoardDim = 5
    obstacles: dict[str, list[tuple[int, int]]] = {}
    robots: list[ConfigRobot] = []


class FileListResponse(BaseModel):
    files: list[str]


class InstructionsFile(BaseModel):
    commands: list[str]
