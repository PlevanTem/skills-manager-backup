#!/usr/bin/env bash
# 安装 tRPC Agent 评测平台的后端(pip)与前端(npm)发布包（腾讯镜像，取最新含 beta）。
# 已安装则跳过；加 --upgrade 强制升级。
#
# 用法:
#   bash scripts/install.sh                 # 装后端+前端（缺啥装啥）
#   bash scripts/install.sh --backend-only  # 只装后端
#   bash scripts/install.sh --upgrade       # 升级到最新
set -euo pipefail

PIP_INDEX="https://mirrors.cloud.tencent.com/pypi/simple/"
PIP_EXTRA="https://mirrors.tencent.com/repository/pypi/tencent_pypi/simple/"
NPM_REGISTRY="https://mirrors.tencent.com/npm/"
FRONTEND_PACKAGE="@tencent/trpc-agent-eval-client"

UPGRADE=""
DO_BACKEND=1
DO_FRONTEND=1
for arg in "$@"; do
  case "$arg" in
    --upgrade) UPGRADE="--upgrade" ;;
    --backend-only) DO_FRONTEND=0 ;;
    --frontend-only) DO_BACKEND=0 ;;
    *) echo "未知参数: $arg" >&2; exit 1 ;;
  esac
done

install_backend() {
  if [ -z "$UPGRADE" ] && command -v trpc-agent-eval-server >/dev/null 2>&1; then
    echo "[backend] 已安装: $(trpc-agent-eval-server --help >/dev/null 2>&1 && echo ok)"
    python3 -c "import trpc_agent_eval_server.version as v; print('[backend] 版本', v.__version__)" 2>/dev/null || true
    return
  fi
  echo "[backend] pip install --pre trpc-agent-eval-server ..."
  pip install $UPGRADE --pre trpc-agent-eval-server \
    --index-url "$PIP_INDEX" \
    --extra-index-url "$PIP_EXTRA"
  python3 -c "import trpc_agent_eval_server.version as v; print('[backend] 版本', v.__version__)" 2>/dev/null || true
}

select_latest_npm_version() {
  node -e '
const fs = require("fs");
const input = fs.readFileSync(0, "utf8").trim();
const versions = JSON.parse(input);
const list = Array.isArray(versions) ? versions : [versions];

function parse(version) {
  const match = String(version).match(/^(\d+)\.(\d+)\.(\d+)(?:-([0-9A-Za-z.-]+))?$/);
  if (!match) return null;
  return {
    raw: version,
    major: Number(match[1]),
    minor: Number(match[2]),
    patch: Number(match[3]),
    pre: match[4] ? match[4].split(".") : [],
  };
}

function compareIdentifier(left, right) {
  const leftNumber = /^\d+$/.test(left);
  const rightNumber = /^\d+$/.test(right);
  if (leftNumber && rightNumber) return Number(left) - Number(right);
  if (leftNumber) return -1;
  if (rightNumber) return 1;
  return left.localeCompare(right);
}

function compareVersion(left, right) {
  for (const key of ["major", "minor", "patch"]) {
    if (left[key] !== right[key]) return left[key] - right[key];
  }
  if (left.pre.length === 0 && right.pre.length === 0) return 0;
  if (left.pre.length === 0) return 1;
  if (right.pre.length === 0) return -1;
  const length = Math.max(left.pre.length, right.pre.length);
  for (let index = 0; index < length; index += 1) {
    if (left.pre[index] === undefined) return -1;
    if (right.pre[index] === undefined) return 1;
    const result = compareIdentifier(left.pre[index], right.pre[index]);
    if (result !== 0) return result;
  }
  return 0;
}

const latest = list.map(parse).filter(Boolean).sort(compareVersion).pop();
if (!latest) process.exit(1);
process.stdout.write(latest.raw);
'
}

resolve_latest_frontend_version() {
  npm view "$FRONTEND_PACKAGE" versions --json --registry="$NPM_REGISTRY" | select_latest_npm_version
}

install_frontend() {
  if ! command -v npm >/dev/null 2>&1; then
    echo "[frontend] 未检测到 npm（需 Node.js 20+）。仅做 API 集成可跳过前端。" >&2
    return
  fi
  if [ -z "$UPGRADE" ] && command -v trpc-agent-eval-client >/dev/null 2>&1; then
    echo "[frontend] 已安装: trpc-agent-eval-client"
    return
  fi
  local version
  version="$(resolve_latest_frontend_version)"
  echo "[frontend] npm install -g ${FRONTEND_PACKAGE}@${version} ..."
  npm install -g "${FRONTEND_PACKAGE}@${version}" --registry="$NPM_REGISTRY"
}

[ "$DO_BACKEND" -eq 1 ] && install_backend
[ "$DO_FRONTEND" -eq 1 ] && install_frontend
echo "[done] 安装完成。下一步: bash scripts/serve.sh"
