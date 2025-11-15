from __future__ import annotations

import sys

from .cli import run as run_cli


def main() -> None:
    code = run_cli(sys.argv[1:])
    raise SystemExit(code)
