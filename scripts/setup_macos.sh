#!/usr/bin/env bash
set -euo pipefail

# One-click setup for macOS
DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
ROOT=$(cd "$DIR/.." && pwd)
cd "$ROOT"

# Choose Python 3.11+ if available
PY=${PYTHON:-}
if [[ -z "$PY" ]]; then
  if command -v python3.12 >/dev/null 2>&1; then
    PY=python3.12
  elif command -v python3.11 >/dev/null 2>&1; then
    PY=python3.11
  else
    PY=python3
  fi
fi

# Check version >= 3.11
ver=$($PY -c 'import sys; print("%d.%d"%sys.version_info[:2])' || echo "0.0")
major=${ver%%.*}
minor=${ver##*.}
if [[ "$major" -lt 3 || "$minor" -lt 11 ]]; then
  echo "需要 Python 3.11+，当前版本: $ver" >&2
  exit 1
fi

VENV_DIR="$ROOT/.venv"
if [[ ! -d "$VENV_DIR" ]]; then
  echo "创建虚拟环境: $VENV_DIR"
  $PY -m venv "$VENV_DIR"
fi

# shellcheck disable=SC1090
source "$VENV_DIR/bin/activate"

python -m pip install --upgrade pip >/dev/null
# No external deps required

echo "环境就绪。"

if [[ "${1:-}" == "gui" ]]; then
  echo "启动 GUI…"
  python -m dfu_guide.gui
elif [[ "${1:-}" == "cli" ]]; then
  shift || true
  echo "启动 CLI…"
  python -m dfu_guide.cli "$@"
else
  echo "可执行:"
  echo "  bash scripts/run_gui.sh"
  echo "  bash scripts/run_cli.sh guide --family face"
fi
