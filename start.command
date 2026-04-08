#!/bin/zsh

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$SCRIPT_DIR"
cd "$PROJECT_ROOT"

APP_HOST="${APP_HOST:-127.0.0.1}"
APP_PORT="${APP_PORT:-8000}"

port_pid() {
  lsof -nP -iTCP:"$1" -sTCP:LISTEN -t 2>/dev/null | head -n 1
}

is_hireme_running() {
  python3 - "$APP_HOST" "$1" <<'PY'
import json
import sys
import urllib.request

host = sys.argv[1]
port = sys.argv[2]
url = f"http://{host}:{port}/api/schema"

try:
    with urllib.request.urlopen(url, timeout=2) as response:
        payload = json.load(response)
except Exception:
    sys.exit(1)

if isinstance(payload, dict) and "blueprint" in payload and "data" in payload:
    sys.exit(0)
sys.exit(1)
PY
}

find_next_free_port() {
  local port="$1"
  while [ "$port" -le 8100 ]; do
    if [ -z "$(port_pid "$port")" ]; then
      echo "$port"
      return 0
    fi
    port=$((port + 1))
  done
  return 1
}

if ! python3 -c "import uvicorn" >/dev/null 2>&1; then
  echo "Installing dependencies..."
  python3 -m pip install -r requirements.txt
fi

EXISTING_PID="$(port_pid "$APP_PORT")"

if [ -n "$EXISTING_PID" ]; then
  if is_hireme_running "$APP_PORT"; then
    echo "The service is already running."
    echo "URL: http://$APP_HOST:$APP_PORT"
    open "http://$APP_HOST:$APP_PORT"
    exit 0
  fi

  NEXT_PORT="$(find_next_free_port $((APP_PORT + 1)))" || {
    echo "Ports 8000-8100 are all in use. Please close one of those services and try again."
    exit 1
  }
  echo "Port $APP_PORT is in use by another process. Switching to port $NEXT_PORT."
  APP_PORT="$NEXT_PORT"
fi

echo "Starting the service..."
echo "URL: http://$APP_HOST:$APP_PORT"

(sleep 2 && open "http://$APP_HOST:$APP_PORT") >/dev/null 2>&1 &

python3 -m uvicorn app.main:app --reload --host "$APP_HOST" --port "$APP_PORT"
