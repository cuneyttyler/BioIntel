.PHONY: build serve start dev

# Build frontend + collect static + migrate
build:
	@source venv/bin/activate && bash scripts/build.sh

# Start gunicorn + localtunnel (requires: make build first)
serve:
	@source venv/bin/activate && bash scripts/serve.sh

# Build then serve in one command
start: build serve

# Local dev mode (Vite dev server + Django runserver, no tunnel)
dev:
	@echo "Starting Django dev server on :8000 ..."
	@source venv/bin/activate && python manage.py runserver &
	@echo "Starting Vite dev server on :5173 ..."
	@cd frontend && npm run dev
