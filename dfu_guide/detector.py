from __future__ import annotations

import platform
import re
import subprocess
import threading
import time
from dataclasses import dataclass
from enum import Enum, auto
from typing import Callable, Optional, Tuple

from .utils import get_logger, is_macos


class DeviceState(Enum):
    UNKNOWN = auto()
    NORMAL = auto()
    RECOVERY = auto()
    DFU = auto()


SP_CMD = ["system_profiler", "SPUSBDataType"]
IOREG_CMD = ["ioreg", "-p", "IOUSB", "-l"]


@dataclass
class DetectResult:
    state: DeviceState
    raw_sp: str = ""
    raw_ioreg: str = ""
    matched_lines: str = ""


def run_cmd(cmd: list[str], timeout: float = 4.0) -> Tuple[int, str, str]:
    try:
        p = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
            check=False,
            text=True,
        )
        return p.returncode, p.stdout or "", p.stderr or ""
    except Exception as e:
        return 1, "", str(e)


# Parsing helpers kept public for unit tests

def parse_system_profiler(text: str) -> DeviceState:
    t = text or ""
    t_low = t.lower()

    # Strong matches
    if re.search(r"dfu", t_low):
        return DeviceState.DFU
    if re.search(r"recovery\s*mode", t_low):
        return DeviceState.RECOVERY

    # Generic Apple Mobile Device without DFU/Recovery markers
    if re.search(r"apple\s+mobile\s+device|iphone|ipad", t_low):
        return DeviceState.NORMAL

    return DeviceState.UNKNOWN


def parse_ioreg(text: str) -> DeviceState:
    t = text or ""
    t_low = t.lower()

    if re.search(r"dfu", t_low):
        return DeviceState.DFU
    if re.search(r"recovery\s*mode", t_low) or re.search(r"\(recovery\)", t_low):
        return DeviceState.RECOVERY
    if re.search(r"apple\s+mobile\s+device|iphone|ipad", t_low):
        return DeviceState.NORMAL

    return DeviceState.UNKNOWN


def detect_once() -> DetectResult:
    logger = get_logger()
    if not is_macos():
        logger.debug("Not macOS; returning UNKNOWN state.")
        return DetectResult(DeviceState.UNKNOWN)

    rc1, out1, err1 = run_cmd(SP_CMD)
    rc2, out2, err2 = run_cmd(IOREG_CMD)

    # Collect lines with potential matches for logging
    matched = []
    for src, out in (("SP", out1), ("IOREG", out2)):
        for line in (out or "").splitlines():
            l = line.strip()
            if not l:
                continue
            ll = l.lower()
            if ("dfu" in ll) or ("recovery" in ll) or ("apple mobile device" in ll) or ("iphone" in ll):
                matched.append(f"[{src}] {l}")

    # Merge parsing
    st1 = parse_system_profiler(out1)
    st2 = parse_ioreg(out2)

    # Heuristic merge preferring higher certainty
    if DeviceState.DFU in (st1, st2):
        st = DeviceState.DFU
    elif DeviceState.RECOVERY in (st1, st2):
        st = DeviceState.RECOVERY
    elif DeviceState.NORMAL in (st1, st2):
        st = DeviceState.NORMAL
    else:
        st = DeviceState.UNKNOWN

    if err1:
        matched.append(f"[SP:ERR] {err1.strip()}")
    if err2:
        matched.append(f"[IOREG:ERR] {err2.strip()}")

    return DetectResult(state=st, raw_sp=out1, raw_ioreg=out2, matched_lines="\n".join(matched))


class Detector(threading.Thread):
    def __init__(self, interval: float = 0.5, callback: Optional[Callable[[DetectResult], None]] = None):
        super().__init__(daemon=True)
        self.interval = max(0.25, float(interval))
        self._callback = callback
        self._stop = threading.Event()
        self._last_state: Optional[DeviceState] = None
        self.logger = get_logger()

    def run(self) -> None:
        while not self._stop.is_set():
            res = detect_once()
            if self._callback:
                try:
                    self._callback(res)
                except Exception as e:
                    self.logger.warning("Detector callback error: %s", e)

            if res.state != self._last_state:
                self.logger.info("State changed: %s -> %s", self._last_state, res.state)
                if res.matched_lines:
                    self.logger.info("Relevant USB entries:\n%s", res.matched_lines)
                self._last_state = res.state

            time.sleep(self.interval)

    def stop(self) -> None:
        self._stop.set()
