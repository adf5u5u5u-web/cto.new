from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Callable, Generator, List, Optional, Tuple

from .audio import beep, say
from .utils import get_logger


@dataclass
class Step:
    name: str
    duration: int  # seconds
    instruction: str


GuideTick = Tuple[int, int, str]  # (remaining_in_step, elapsed_total, message)


FAMILIES = {
    "6s": "iPhone 6s/earlier (Home button)",
    "7": "iPhone 7/7 Plus",
    "8": "iPhone 8/SE2/SE3 and pre-Face ID layout",
    "faceid": "Face ID series (X/XS/11/12/13/14/15)",
}


def get_schedule(family: str) -> List[Step]:
    f = family.lower().strip()

    if f == "6s":
        return [
            Step("hold_power_home", 8, "Press and hold Power + Home for 8 seconds"),
            Step("release_power_hold_home", 10, "Release Power; keep holding Home for 10 seconds"),
        ]
    if f == "7":
        return [
            Step("hold_side_vol_down", 8, "Press and hold Side + Volume Down for 8 seconds"),
            Step("release_side_hold_vol_down", 10, "Release Side; keep holding Volume Down for 10 seconds"),
        ]
    if f in ("8", "faceid"):
        # Common DFU rhythm for 8/SE2/SE3 and Face ID
        # Quick: Vol Up, then Vol Down (no hold) -> Hold Side until screen goes black
        # Then hold Side + Vol Down for 5s -> release Side, keep holding Vol Down for 10s
        return [
            Step("quick_vol_up", 1, "Quickly press Volume Up (tap)"),
            Step("quick_vol_down", 1, "Quickly press Volume Down (tap)"),
            Step("hold_side_until_black", 3, "Press and hold Side until screen goes black (~3s)"),
            Step("hold_side_vol_down", 5, "Continue holding Side and also hold Volume Down for 5 seconds"),
            Step("release_side_hold_vol_down", 10, "Release Side; keep holding Volume Down for 10 seconds"),
        ]

    # Default empty schedule
    return []


def guide_generator(
    family: str,
    on_tick: Optional[Callable[[GuideTick], None]] = None,
    use_beep: bool = False,
    use_voice: bool = False,
) -> Generator[GuideTick, None, None]:
    logger = get_logger()
    schedule = get_schedule(family)
    elapsed_total = 0
    if not schedule:
        return

    # Announce start
    start_msg = f"Starting DFU guide for '{family}'"
    logger.info(start_msg)
    if use_voice:
        say(start_msg)

    for step in schedule:
        remaining = step.duration
        # Step announcement
        logger.info("Step: %s - %s", step.name, step.instruction)
        if use_voice:
            say(step.instruction)
        while remaining > 0:
            msg = f"{step.instruction} | {remaining}s"
            tick: GuideTick = (remaining, elapsed_total, msg)
            if on_tick:
                try:
                    on_tick(tick)
                except Exception:
                    pass
            if use_beep:
                beep()
            else:
                # Optionally speak the countdown numbers (may be noisy)
                if use_voice and remaining <= 3:
                    say(str(remaining))
            time.sleep(1)
            remaining -= 1
            elapsed_total += 1
            yield tick

    finish_msg = "Guide finished. Check device state: black screen indicates DFU if detected."
    logger.info(finish_msg)
    if use_voice:
        say("Guide finished. Check DFU state.")


def run_guide_blocking(
    family: str,
    on_tick: Optional[Callable[[GuideTick], None]] = None,
    use_beep: bool = False,
    use_voice: bool = False,
) -> None:
    for _ in guide_generator(family, on_tick=on_tick, use_beep=use_beep, use_voice=use_voice):
        pass
