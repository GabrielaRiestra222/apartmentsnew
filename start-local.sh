#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECTS_DIR="$(cd "$ROOT_DIR/.." && pwd)"
LANDING_DIR="$PROJECTS_DIR/ApartmentsLanding"
DASHBOARD_DIR="$PROJECTS_DIR/SaaS Property Management Dashboard"

cleanup() {
  if [[ -n "${BACKEND_PID:-}" ]]; then
    kill "$BACKEND_PID" 2>/dev/null || true
  fi
  if [[ -n "${LANDING_PID:-}" ]]; then
    kill "$LANDING_PID" 2>/dev/null || true
  fi
  if [[ -n "${DASHBOARD_PID:-}" ]]; then
    kill "$DASHBOARD_PID" 2>/dev/null || true
  fi
}
trap cleanup EXIT INT TERM

cd "$ROOT_DIR"
USE_SQLITE=True ./venv/bin/python manage.py migrate
USE_SQLITE=True ./venv/bin/python manage.py runserver 127.0.0.1:8000 &
BACKEND_PID=$!

cd "$LANDING_DIR"
npm run dev -- --host 127.0.0.1 --port 3000 &
LANDING_PID=$!

cd "$DASHBOARD_DIR"
VITE_API_BASE_URL=http://127.0.0.1:8000/api npm run dev -- --host 127.0.0.1 --port 5174 &
DASHBOARD_PID=$!

echo "Backend:  http://127.0.0.1:8000/"
echo "API:      http://127.0.0.1:8000/api/public/properties/"
echo "Landing:  http://127.0.0.1:3000/"
echo "CRM/CMS:  http://127.0.0.1:5174/"
echo
echo "Press Ctrl+C to stop all servers."

wait
