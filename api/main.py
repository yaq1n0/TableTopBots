from __future__ import annotations

import re
from pathlib import Path

from fastapi import FastAPI, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from core.engine import simulate
from core.models import (
    ConfigFile,
    FileListResponse,
    InstructionsFile,
    ParseFileResponse,
    SimulationRequest,
    SimulationResponse,
    ValidateRequest,
    ValidationResponse,
)
from core.parsing import is_valid_command

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
SAFE_NAME = re.compile(r"^[a-zA-Z0-9_-]+$")

app = FastAPI(title="TableTopBotsAPI")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/simulate", response_model=SimulationResponse)
def run_simulation(request: SimulationRequest):
    return simulate(request)


@app.post("/validate", response_model=ValidationResponse)
def validate_command(body: ValidateRequest):
    valid = is_valid_command(body.command)
    if valid:
        return {"valid": True}
    return {"valid": False, "error": "Invalid command format"}


@app.post("/parse-file", response_model=ParseFileResponse)
async def parse_file(file: UploadFile):
    content = await file.read()
    text = content.decode("utf-8")
    commands = [line.strip() for line in text.splitlines() if line.strip()]
    return {"commands": commands}


def _validate_name(name: str) -> None:
    if not SAFE_NAME.match(name):
        raise HTTPException(400, "Invalid file name")


# --- Config file endpoints ---


@app.get("/data/configs", response_model=FileListResponse)
def list_configs():
    files = sorted(p.stem for p in DATA_DIR.glob("*.json"))
    return {"files": files}


@app.get("/data/configs/{name}", response_model=ConfigFile)
def load_config(name: str):
    _validate_name(name)
    path = DATA_DIR / f"{name}.json"
    if not path.exists():
        raise HTTPException(404, "Config not found")
    return ConfigFile.model_validate_json(path.read_text("utf-8"))


@app.post("/data/configs/{name}", response_model=ConfigFile)
def save_config(name: str, config: ConfigFile):
    _validate_name(name)
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    path = DATA_DIR / f"{name}.json"
    path.write_text(config.model_dump_json(indent=2), encoding="utf-8")
    return config


# --- Instruction file endpoints ---


@app.get("/data/instructions", response_model=FileListResponse)
def list_instructions():
    files = sorted(p.stem for p in DATA_DIR.glob("*.txt"))
    return {"files": files}


@app.get("/data/instructions/{name}", response_model=InstructionsFile)
def load_instructions(name: str):
    _validate_name(name)
    path = DATA_DIR / f"{name}.txt"
    if not path.exists():
        raise HTTPException(404, "Instructions not found")
    text = path.read_text("utf-8")
    commands = [line.strip() for line in text.splitlines() if line.strip()]
    return {"commands": commands}


@app.post("/data/instructions/{name}", response_model=InstructionsFile)
def save_instructions(name: str, body: InstructionsFile):
    _validate_name(name)
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    path = DATA_DIR / f"{name}.txt"
    path.write_text("\n".join(body.commands) + "\n", encoding="utf-8")
    return body
