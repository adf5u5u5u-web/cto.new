from __future__ import annotations

import argparse
import sys
import threading
import time
from typing import Optional

from .audio import beep, say
from .detector import DeviceState, DetectResult, Detector
from .guide import FAMILIES, run_guide_blocking
from .utils import get_logger


EXIT_OK = 0
EXIT_FAIL = 1
EXIT_RECOVERY = 2


class StateWatcher:
    def __init__(self, stable_seconds: float = 1.0):
        self.current: DeviceState = DeviceState.UNKNOWN
        self._last_change_ts: float = time.time()
        self._stable_seconds = stable_seconds

    def update(self, state: DeviceState) -> None:
        if state != self.current:
            self.current = state
            self._last_change_ts = time.time()

    def stable_for(self) -> float:
        return time.time() - self._last_change_ts


class CLI:
    def __init__(self, family: Optional[str], interval: float, use_beep: bool, use_voice: bool):
        self.logger = get_logger()
        self.family = family
        self.interval = interval
        self.use_beep = use_beep
        self.use_voice = use_voice
        self.detector = Detector(interval=interval, callback=self.on_detect)
        self.watcher = StateWatcher(stable_seconds=1.0)
        self._stop = threading.Event()

    def on_detect(self, res: DetectResult) -> None:
        self.watcher.update(res.state)
        status = res.state.name
        sys.stdout.write(f"\rDevice state: {status:<8} | polling {self.interval:.2f}s    ")
        sys.stdout.flush()

    def start(self) -> int:
        self.detector.start()
        self.logger.info("CLI started: family=%s, interval=%s, beep=%s, voice=%s", self.family, self.interval, self.use_beep, self.use_voice)

        guide_thread: Optional[threading.Thread] = None
        if self.family:
            def on_tick(tick):
                remaining, elapsed_total, msg = tick
                sys.stdout.write(f"\n{msg}")
                sys.stdout.flush()
            guide_thread = threading.Thread(target=run_guide_blocking, args=(self.family,), kwargs={"on_tick": on_tick, "use_beep": self.use_beep, "use_voice": self.use_voice}, daemon=True)
            guide_thread.start()
        else:
            print("\nTip: pass --family to receive per-second DFU guidance.")

        try:
            # Loop until DFU or Recovery (stable)
            while not self._stop.is_set():
                st = self.watcher.current
                stable = self.watcher.stable_for()
                if st == DeviceState.DFU and stable >= 0.5:
                    print("\nDFU detected! You can release buttons now. To exit DFU: quick Volume Up, quick Volume Down, then hold Side until Apple logo.")
                    if self.use_beep:
                        beep()
                    if self.use_voice:
                        say("DFU mode detected")
                    return EXIT_OK
                if st == DeviceState.RECOVERY and stable >= 1.0:
                    print("\nEntered Recovery Mode instead of DFU. Try again and pay attention to the release timing.")
                    if self.use_beep:
                        beep()
                    return EXIT_RECOVERY
                time.sleep(0.1)
        except KeyboardInterrupt:
            print("\nInterrupted by user.")
        finally:
            self.detector.stop()
            if guide_thread and guide_thread.is_alive():
                # Best effort; guide thread will finish on its own
                pass
        return EXIT_FAIL


def parse_args(argv: list[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(prog="dfu_guide", description="macOS iPhone DFU guide tool (CLI/GUI)")
    p.add_argument("--mode", choices=["cli", "gui"], default="cli", help="Run mode: CLI or GUI")
    p.add_argument("--family", choices=["6s", "7", "8", "faceid"], help="Model family for DFU guidance")
    p.add_argument("--voice", choices=["on", "off"], default="off", help="Voice prompts via osascript")
    p.add_argument("--beep", choices=["on", "off"], default="on", help="Beep per second via afplay")
    p.add_argument("--interval", type=float, default=0.5, help="Polling interval in seconds (0.25–0.5 recommended)")
    return p.parse_args(argv)


def run(argv: list[str]) -> int:
    ns = parse_args(argv)
    if ns.mode == "gui":
        from .gui import run as run_gui
        return run_gui()

    use_voice = ns.voice == "on"
    use_beep = ns.beep == "on"

    cli = CLI(ns.family, ns.interval, use_beep, use_voice)
    code = cli.start()
    return code
