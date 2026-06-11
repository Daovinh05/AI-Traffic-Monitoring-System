#!/usr/bin/env bash
set -u

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_PORT="${PORT:-5001}"
FRONTEND_PORT="3001"
BACKEND_PID=""
FRONTEND_PID=""

log() {
  printf '[START] %s\n' "$1"
}

fail() {
  printf '[ERROR] %s\n' "$1" >&2
  exit 1
}

check_port() {
  local port="$1"
  local process

  process="$(lsof -nP -iTCP:"$port" -sTCP:LISTEN 2>/dev/null || true)"
  if [ -n "$process" ]; then
    printf '[ERROR] Cổng %s đang được sử dụng:\n%s\n' "$port" "$process" >&2
    return 1
  fi
}

cleanup() {
  trap - INT TERM EXIT
  printf '\n'
  log "Đang dừng frontend và backend..."

  if [ -n "$FRONTEND_PID" ] && kill -0 "$FRONTEND_PID" 2>/dev/null; then
    kill "$FRONTEND_PID" 2>/dev/null || true
  fi

  if [ -n "$BACKEND_PID" ] && kill -0 "$BACKEND_PID" 2>/dev/null; then
    kill "$BACKEND_PID" 2>/dev/null || true
  fi

  wait "$FRONTEND_PID" 2>/dev/null || true
  wait "$BACKEND_PID" 2>/dev/null || true
  log "Đã dừng hệ thống."
}

command -v lsof >/dev/null 2>&1 || fail "Không tìm thấy lệnh lsof."
command -v npm >/dev/null 2>&1 || fail "Không tìm thấy npm."

[ -x "$PROJECT_ROOT/.venv/bin/python" ] || fail \
  "Không tìm thấy .venv/bin/python. Hãy tạo và cài môi trường Python trước."

[ -f "$PROJECT_ROOT/frontend/package.json" ] || fail \
  "Không tìm thấy frontend/package.json."

[ -d "$PROJECT_ROOT/frontend/node_modules" ] || fail \
  "Frontend chưa có node_modules. Chạy: cd frontend && npm install"

check_port "$BACKEND_PORT" || exit 1
check_port "$FRONTEND_PORT" || exit 1

mkdir -p "$PROJECT_ROOT/.cache/ai-traffic"

trap cleanup INT TERM EXIT

log "Khởi động backend tại http://localhost:$BACKEND_PORT ..."
(
  cd "$PROJECT_ROOT" || exit 1
  export AI_TRAFFIC_CACHE_DIR="$PROJECT_ROOT/.cache/ai-traffic"
  export PYGAME_HIDE_SUPPORT_PROMPT=1
  exec "$PROJECT_ROOT/.venv/bin/python" -m backend.app.main
) &
BACKEND_PID=$!

log "Khởi động frontend tại http://localhost:$FRONTEND_PORT ..."
(
  cd "$PROJECT_ROOT/frontend" || exit 1
  exec npm run dev
) &
FRONTEND_PID=$!

printf '\n'
log "Hệ thống đang chạy:"
printf '  Frontend: http://localhost:%s\n' "$FRONTEND_PORT"
printf '  Backend:  http://localhost:%s\n' "$BACKEND_PORT"
printf '  Đăng nhập: http://localhost:%s/login\n' "$FRONTEND_PORT"
log "Nhấn Ctrl+C để dừng cả hai."
printf '\n'

while true; do
  if ! kill -0 "$BACKEND_PID" 2>/dev/null; then
    wait "$BACKEND_PID"
    status=$?
    fail "Backend đã dừng với mã lỗi $status."
  fi

  if ! kill -0 "$FRONTEND_PID" 2>/dev/null; then
    wait "$FRONTEND_PID"
    status=$?
    fail "Frontend đã dừng với mã lỗi $status."
  fi

  sleep 1
done
