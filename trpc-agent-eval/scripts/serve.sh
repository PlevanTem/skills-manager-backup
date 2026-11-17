#!/usr/bin/env bash
# 启动前后端：先探活，已运行则复用并打印地址，不重复占端口；否则后台启动。
# 日志落到 workdir/logs（默认 ~/.trpc-agent-eval/logs）。
#
# 用法:
#   bash scripts/serve.sh                        # 本机默认端口启动前后端
#   BACKEND_PORT=9001 FRONTEND_PORT=9000 bash scripts/serve.sh
#   BACKEND_HOST=0.0.0.0 FRONTEND_HOST=0.0.0.0 bash scripts/serve.sh   # 自动探测访问 IP
#   PUBLIC_HOST=<业务可访问IP或域名> BACKEND_HOST=0.0.0.0 FRONTEND_HOST=0.0.0.0 bash scripts/serve.sh
#   bash scripts/serve.sh --backend-only
set -euo pipefail

BACKEND_HOST="${BACKEND_HOST:-127.0.0.1}"
BACKEND_PORT="${BACKEND_PORT:-8080}"
FRONTEND_HOST="${FRONTEND_HOST:-127.0.0.1}"
FRONTEND_PORT="${FRONTEND_PORT:-5173}"
PUBLIC_HOST="${PUBLIC_HOST:-}"
WORKDIR="${TRPC_AGENT_EVAL_WORKDIR:-$HOME/.trpc-agent-eval}"
LOG_DIR="$WORKDIR/logs"
URL_FILE="$WORKDIR/ui_urls.json"
BACKEND_URL="http://${BACKEND_HOST}:${BACKEND_PORT}"
# 探活用：0.0.0.0 不能直接 curl，换 127.0.0.1
PROBE_HOST="$BACKEND_HOST"; [ "$PROBE_HOST" = "0.0.0.0" ] && PROBE_HOST="127.0.0.1"
PROBE_URL="http://${PROBE_HOST}:${BACKEND_PORT}"
CLIENT_BACKEND_URL="${TRPC_AGENT_EVAL_BACKEND_URL:-$PROBE_URL}"
if [ -z "$PUBLIC_HOST" ] && { [ "$BACKEND_HOST" = "0.0.0.0" ] || [ "$FRONTEND_HOST" = "0.0.0.0" ]; }; then
  PUBLIC_HOST="$(hostname -I 2>/dev/null | awk '{print $1}')"
  if [ -z "$PUBLIC_HOST" ] && command -v ip >/dev/null 2>&1; then
    PUBLIC_HOST="$(ip route get 1 2>/dev/null | awk '{for(i=1;i<=NF;i++) if($i=="src"){print $(i+1); exit}}')"
  fi
fi
PUBLIC_FRONTEND_HOST="$FRONTEND_HOST"
[ -n "$PUBLIC_HOST" ] && PUBLIC_FRONTEND_HOST="$PUBLIC_HOST"
[ "$PUBLIC_FRONTEND_HOST" = "0.0.0.0" ] && PUBLIC_FRONTEND_HOST="<本机IP>"
PUBLIC_BACKEND_HOST="$BACKEND_HOST"
[ -n "$PUBLIC_HOST" ] && PUBLIC_BACKEND_HOST="$PUBLIC_HOST"
[ "$PUBLIC_BACKEND_HOST" = "0.0.0.0" ] && PUBLIC_BACKEND_HOST="<本机IP>"
PUBLIC_FRONTEND_URL="http://${PUBLIC_FRONTEND_HOST}:${FRONTEND_PORT}/"
PUBLIC_BACKEND_URL="http://${PUBLIC_BACKEND_HOST}:${BACKEND_PORT}"

DO_FRONTEND=1
FRONTEND_READY=0
for arg in "$@"; do
  case "$arg" in
    --backend-only) DO_FRONTEND=0 ;;
    *) echo "未知参数: $arg" >&2; exit 1 ;;
  esac
done

mkdir -p "$LOG_DIR"

health_ok() { curl -fsS "$1/api/health" 2>/dev/null | grep -q '"ok"'; }

port_listens_publicly() {
  port="$1"
  command -v ss >/dev/null 2>&1 || return 0
  ss -ltn "sport = :$port" 2>/dev/null \
    | awk 'NR>1 {print $4}' \
    | grep -Eq '(^|:)0\.0\.0\.0:' || ss -ltn "sport = :$port" 2>/dev/null \
    | awk 'NR>1 {print $4}' \
    | grep -Eq '(^|:)\*:|\[::\]:'
}

start_backend() {
  if health_ok "$PROBE_URL"; then
    echo "[backend] 已在运行，复用 $PROBE_URL"
    return
  fi
  echo "[backend] 启动中 -> $BACKEND_URL (日志 $LOG_DIR/server.log)"
  nohup trpc-agent-eval-server --host "$BACKEND_HOST" --port "$BACKEND_PORT" \
    --log-file "$LOG_DIR/server.log" >>"$LOG_DIR/server.out" 2>&1 &
  for _ in $(seq 1 30); do
    health_ok "$PROBE_URL" && { echo "[backend] 就绪 $PROBE_URL/api/health"; return; }
    sleep 1
  done
  echo "[backend] 启动超时，请查看 $LOG_DIR/server.log" >&2
  exit 1
}

start_frontend() {
  if ! command -v trpc-agent-eval-client >/dev/null 2>&1; then
    echo "[frontend] 未安装 trpc-agent-eval-client，跳过（仅 API 集成可不装）。"
    return
  fi
  if curl -fsS "http://${FRONTEND_HOST/0.0.0.0/127.0.0.1}:${FRONTEND_PORT}/" >/dev/null 2>&1; then
    if [ "$FRONTEND_HOST" = "0.0.0.0" ] && ! port_listens_publicly "$FRONTEND_PORT"; then
      echo "[frontend] 端口 $FRONTEND_PORT 已有本机服务，但未监听 0.0.0.0；远程访问不可用。请停止旧前端或换 FRONTEND_PORT。" >&2
      exit 1
    fi
    echo "[frontend] 端口 $FRONTEND_PORT 已有服务，复用。"
    FRONTEND_READY=1
    return
  fi
  echo "[frontend] 启动中 -> http://${FRONTEND_HOST}:${FRONTEND_PORT}/ (日志 $LOG_DIR/client.log)"
  nohup trpc-agent-eval-client --backend "$CLIENT_BACKEND_URL" \
    --host "$FRONTEND_HOST" --port "$FRONTEND_PORT" \
    --log-file "$LOG_DIR/client.log" >>"$LOG_DIR/client.out" 2>&1 &
  sleep 2
  FRONTEND_READY=1
  echo "[frontend] 浏览器访问 $PUBLIC_FRONTEND_URL"
}

write_url_file() {
  frontend_json=null
  if [ "$FRONTEND_READY" -eq 1 ]; then
    frontend_json="\"$PUBLIC_FRONTEND_URL\""
  fi
  cat >"$URL_FILE" <<EOF
{
  "frontend_url": $frontend_json,
  "backend_url": "$PUBLIC_BACKEND_URL",
  "probe_backend_url": "$PROBE_URL",
  "logs_dir": "$LOG_DIR"
}
EOF
}

start_backend
[ "$DO_FRONTEND" -eq 1 ] && start_frontend
write_url_file
if [ "$FRONTEND_READY" -eq 1 ]; then
  echo "[done] backend=$PUBLIC_BACKEND_URL  frontend=$PUBLIC_FRONTEND_URL"
  echo "[done] URL 记录: $URL_FILE"
else
  echo "[done] backend=$PUBLIC_BACKEND_URL  frontend=未启动"
  echo "[done] URL 记录: $URL_FILE"
fi
echo "提示: 用 python3 scripts/doctor.py --base-url $PROBE_URL 做体检。"
