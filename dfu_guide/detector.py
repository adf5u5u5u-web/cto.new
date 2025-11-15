import re
import threading
import time
from dataclasses import dataclass
from enum import Enum
from typing import Callable, Optional, Tuple

from .utils import get_logger, is_macos, run_cmd


logger = get_logger()


class Mode(str, Enum):
    UNKNOWN = "UNKNOWN"
    DISCONNECTED = "DISCONNECTED"
    NORMAL = "NORMAL"
    RECOVERY = "RECOVERY"
    DFU = "DFU"


@dataclass
class DetectionResult:
    mode: Mode
    source: str
    raw_excerpt: str = ""


def _call_system_profiler() -> Tuple[int, str]:
    code, out, err = run_cmd(["system_profiler", "SPUSBDataType"])
    return code, out or err


def _call_ioreg() -> Tuple[int, str]:
    code, out, err = run_cmd(["ioreg", "-p", "IOUSB", "-l"])
    return code, out or err


def _parse_mode_from_text(text: str) -> Mode:
    t = text
    # Normalize
    t_low = t.lower()

    # DFU detection
    if re.search(r"dfu", t_low):
        return Mode.DFU

    # Recovery
    if re.search(r"recovery|restore|iboot", t_low):
        return Mode.RECOVERY

    # Normal attached iPhone
    if re.search(r"iphone|apple mobile device", t_low):
        return Mode.NORMAL

    # Nothing found
    return Mode.DISCONNECTED


class Detector:
    def __init__(self, interval: float = 0.5, on_change: Optional[Callable[[DetectionResult], None]] = None):
        self.interval = max(0.2, interval)
        self.on_change = on_change
        self._thread: Optional[threading.Thread] = None
        self._stop = threading.Event()
        self._latest: DetectionResult = DetectionResult(Mode.UNKNOWN, source="init")

    @property
    def latest(self) -> DetectionResult:
        return self._latest

    def detect_once(self) -> DetectionResult:
        if not is_macos():
            # Best effort on non-macOS environments
            return DetectionResult(Mode.UNKNOWN, source="non-macos")

        best = DetectionResult(Mode.DISCONNECTED, source="none")

        try:
            code1, out1 = _call_system_profiler()
            if code1 == 0:
                m1 = _parse_mode_from_text(out1)
                if _is_better(m1, best.mode):
                    best = DetectionResult(m1, source="system_profiler", raw_excerpt=_short_excerpt(out1))
        except Exception:
            pass

        try:
            code2, out2 = _call_ioreg()
            if code2 == 0:
                m2 = _parse_mode_from_text(out2)
                if _is_better(m2, best.mode):
                    best = DetectionResult(m2, source="ioreg", raw_excerpt=_short_excerpt(out2))
        except Exception:
            pass

        # If nothing matched but commands ran, keep DISCONNECTED
        logger.debug(f"detect_once -> {best.mode} via {best.source}")
        return best

    def start(self):
        if self._thread and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._run, name="DFUDetector", daemon=True)
        self._thread.start()

    def stop(self):
        self._stop.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=self.interval * 4)

    def _run(self):
        last_mode = None
        while not self._stop.is_set():
            res = self.detect_once()
            self._latest = res
            if res.mode != last_mode:
                logger.info(f"[检测] 状态变更: {res.mode} (via {res.source})")
                last_mode = res.mode
                if self.on_change:
                    try:
                        self.on_change(res)
                    except Exception:
                        pass
            time.sleep(self.interval)


def _is_better(a: Mode, b: Mode) -> bool:
    rank = {
        Mode.DFU: 4,
        Mode.RECOVERY: 3,
        Mode.NORMAL: 2,
        Mode.DISCONNECTED: 1,
        Mode.UNKNOWN: 0,
    }
    return rank[a] > rank[b]


def _short_excerpt(text: str, max_len: int = 500) -> str:
    t = re.sub(r"\s+", " ", text)
    if len(t) > max_len:
        return t[:max_len] + "..."
    return t
