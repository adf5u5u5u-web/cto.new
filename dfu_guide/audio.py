from __future__ import annotations

import shlex
import subprocess
from typing import Optional

from .utils import get_logger, is_macos


DEFAULT_SOUND = "/System/Library/Sounds/Ping.aiff"


def _run(cmd: str) -> None:
    try:
        subprocess.Popen(shlex.split(cmd), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        # Best-effort; ignore errors
        pass


def beep(sound_path: Optional[str] = None) -> None:
    if not is_macos():
        return
    path = sound_path or DEFAULT_SOUND
    _run(f"afplay {shlex.quote(path)}")


def say(text: str) -> None:
    if not is_macos():
        return
    safe = text.replace('"', "'")
    _run(f'osascript -e "say \"{safe}\""')
