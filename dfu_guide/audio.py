import time
from dataclasses import dataclass
from typing import Optional

from .utils import get_logger, is_macos, run_cmd, which


logger = get_logger()


DEFAULT_SOUND = "/System/Library/Sounds/Glass.aiff"


@dataclass
class AudioFeedback:
    beep_enabled: bool = True
    voice_enabled: bool = False

    def beep(self, times: int = 1, interval: float = 0.15):
        if not self.beep_enabled:
            return
        for i in range(max(1, times)):
            _beep_once()
            if i < times - 1:
                time.sleep(interval)

    def speak(self, text: str):
        if not self.voice_enabled:
            return
        _speak_text(text)


def _beep_once():
    if not is_macos():
        # Terminal bell fallback
        print("\a", end="", flush=True)
        return

    # Prefer osascript beep
    if which("osascript"):
        code, out, err = run_cmd(["osascript", "-e", "beep 1"])  # type: ignore[arg-type]
        if code == 0:
            return

    # Fallback to afplay
    if which("afplay"):
        run_cmd(["afplay", DEFAULT_SOUND])
        return

    # Last resort
    print("\a", end="", flush=True)


def _speak_text(text: str):
    if not is_macos():
        logger.info(f"[语音提示] {text}")
        return

    # Prefer osascript to ensure consistent voice
    if which("osascript"):
        # Use Ting-Ting voice if available
        script = f'say "{text}" using "Ting-Ting"'
        run_cmd(["osascript", "-e", script])
        return

    # Fallback to say command
    if which("say"):
        run_cmd(["say", text])
        return

    # Fallback to log
    logger.info(f"[语音提示] {text}")
