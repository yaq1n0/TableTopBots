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


class Command(BaseModel):
    type: Literal["PLACE", "MOVE", "LEFT", "RIGHT", "REPORT"]
    x: int | None = None
    y: int | None = None
    facing: Direction | None = None
    count: int = 1


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


class SimulationRequest(BaseModel):
    width: BoardDim = 5
    height: BoardDim = 5
    obstacles: dict[str, list[tuple[int, int]]] = {}
    robot_names: list[str] = []
    command_stacks: list[list[str | None]] = []


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
