.PHONY: build serve start dev

# Build frontend + collect static + migrate
build:
	@. venv/bin/activate && bash scripts/build.sh

# Start gunicorn + localtunnel (requires: make build first)
# exec replaces the intermediate shell so Ctrl+C goes directly to serve.sh's trap
serve:
	@. venv/bin/activate && exec bash scripts/serve.sh

# Build then serve in one command
start: build serve

# Local dev mode (Vite dev server + Django runserver, no tunnel)
dev:
	@. venv/bin/activate && exec bash scripts/dev.sh
