#!/usr/bin/env bash
set -euo pipefail

DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
ROOT=$(cd "$DIR/.." && pwd)

if [[ ! -d "$ROOT/.venv" ]]; then
  bash "$ROOT/scripts/setup_macos.sh" cli "$@"
  exit 0
fi
# shellcheck disable=SC1090
source "$ROOT/.venv/bin/activate"

python -m dfu_guide.cli "$@"
