.PHONY: install install-dev lint format typecheck test check server client dev clean

# ── Install ──────────────────────────────────────────────
install:
	pip install -e ".[dev]"
	cd ui && npm install

# ── Python ───────────────────────────────────────────────
typecheck:
	pyright

test:
	pytest -v

lint:
	ruff check core/ api/ tests/

lint-fix:
	ruff check core/ api/ tests/ --fix

format:
	ruff format core/ api/ tests/ --check

format-fix:
	ruff format core/ api/ tests/

# ── Dev servers ──────────────────────────────────────────
server:
	uvicorn api.main:app --reload --port 8000

client:
	cd ui && npm run dev


