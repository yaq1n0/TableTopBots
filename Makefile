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

format:
	ruff format core/ api/ tests/

# ── TypeScript ───────────────────────────────────────────
ui-build:
	cd ui && npm run build

ui-typecheck:
	cd ui && npx tsc -b

ui-lint:
	cd ui && npx eslint .

ui-format:
	cd ui && npx prettier --write "src/**/*.{ts,tsx,css}"

# ── Dev servers ──────────────────────────────────────────
server:
	uvicorn api.main:app --reload --port 8000

client:
	cd ui && npm run dev


