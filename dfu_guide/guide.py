import threading
import time
from dataclasses import dataclass
from enum import Enum
from typing import Callable, List, Optional

from .audio import AudioFeedback
from .detector import Detector, Mode
from .utils import get_logger


logger = get_logger()


class Family(str, Enum):
    HOME = "6s/Home"
    SEVEN = "7"
    EIGHT_SE = "8/SE2/SE3"
    FACE_ID = "Face ID (X–15)"


FAMILY_CHOICES = [Family.HOME.value, Family.SEVEN.value, Family.EIGHT_SE.value, Family.FACE_ID.value]


@dataclass
class Step:
    title: str
    seconds: int = 0
    detail: str = ""


@dataclass
class GuidePlan:
    family: Family
    steps: List[Step]


class GuideRunner:
    def __init__(
        self,
        detector: Detector,
        audio: Optional[AudioFeedback] = None,
        on_tick: Optional[Callable[[int, str], None]] = None,
        on_step: Optional[Callable[[Step], None]] = None,
        on_finish: Optional[Callable[[bool, str], None]] = None,
    ):
        self.detector = detector
        self.audio = audio or AudioFeedback()
        self.on_tick = on_tick
        self.on_step = on_step
        self.on_finish = on_finish
        self._stop = threading.Event()
        self._thread: Optional[threading.Thread] = None

    def start(self, family: Family):
        if self._thread and self._thread.is_alive():
            return
        plan = create_plan(family)
        self._stop.clear()
        self._thread = threading.Thread(target=self._run, args=(plan,), name="DFUGuide", daemon=True)
        self._thread.start()

    def stop(self):
        self._stop.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=1.0)

    def _run(self, plan: GuidePlan):
        success = False
        self.audio.speak(f"即将开始 {plan.family.value} 机型 DFU 引导。请严格按照指引操作。")
        # Pre-countdown
        self._emit_step(Step("准备", detail="3 秒后开始"))
        for i in range(3, 0, -1):
            if self._tick(i, "即将开始"):
                return
        # Steps
        for step in plan.steps:
            if self._stop.is_set():
                return
            self._emit_step(step)
            if step.seconds <= 0:
                # Tap/quick step
                self.audio.beep(2)
                time.sleep(0.6)
                # Early DFU detection
                if self.detector.latest.mode == Mode.DFU:
                    success = True
                    break
                continue
            # Timed step countdown
            for s in range(step.seconds, 0, -1):
                if self._tick(s, step.title):
                    return
                # Check DFU during the process to stop early
                if self.detector.latest.mode == Mode.DFU:
                    success = True
                    break
            if success:
                break
        # Post-check result
        final_mode = self.detector.latest.mode
        if success or final_mode == Mode.DFU:
            self.audio.beep(3)
            self.audio.speak("成功进入 DFU 模式。")
            self._emit_finish(True, "成功进入 DFU 模式！")
            return
        if final_mode == Mode.RECOVERY:
            self.audio.beep(1)
            tip = "检测到恢复模式，请在松开电源键的瞬间重试（关键时机）。"
            self._emit_finish(False, tip)
            return
        self._emit_finish(False, "未检测到 DFU，请按指引重新尝试。")

    def _emit_step(self, step: Step):
        logger.info(f"[指引] {step.title} {f'({step.detail})' if step.detail else ''}")
        self.audio.speak(step.title)
        if self.on_step:
            try:
                self.on_step(step)
            except Exception:
                pass

    def _emit_finish(self, ok: bool, msg: str):
        logger.info(f"[完成] {msg}")
        if self.on_finish:
            try:
                self.on_finish(ok, msg)
            except Exception:
                pass

    def _tick(self, sec: int, label: str) -> bool:
        if self._stop.is_set():
            return True
        if self.on_tick:
            try:
                self.on_tick(sec, label)
            except Exception:
                pass
        self.audio.beep(1)
        time.sleep(1)
        return self._stop.is_set()


def create_plan(family: Family) -> GuidePlan:
    if family == Family.HOME:
        steps = [
            Step("连接并关机，准备按键：电源 + Home"),
            Step("同时按住 电源 + Home", seconds=8),
            Step("松开 电源，继续按住 Home", seconds=10),
        ]
    elif family == Family.SEVEN:
        steps = [
            Step("连接并关机，准备按键：音量下 + 侧边键"),
            Step("同时按住 侧边键 + 音量下", seconds=8),
            Step("松开 侧边键，继续按住 音量下", seconds=10),
        ]
    elif family == Family.EIGHT_SE:
        steps = [
            Step("快速按一下 音量上（不要长按）"),
            Step("快速按一下 音量下（不要长按）"),
            Step("按住 侧边键，直到屏幕变黑", seconds=10),
            Step("继续按住 侧边键，同时按住 音量下", seconds=5),
            Step("松开 侧边键，继续按住 音量下", seconds=10),
        ]
    else:  # FACE_ID
        steps = [
            Step("快速按一下 音量上（不要长按）"),
            Step("快速按一下 音量下（不要长按）"),
            Step("按住 侧边键，直到屏幕变黑", seconds=10),
            Step("继续按住 侧边键，同时按住 音量下", seconds=5),
            Step("松开 侧边键，继续按住 音量下", seconds=10),
        ]
    return GuidePlan(family=family, steps=steps)


def family_from_choice(choice: str) -> Family:
    mapping = {
        "home": Family.HOME,
        "6s": Family.HOME,
        "6s/home": Family.HOME,
        "7": Family.SEVEN,
        "seven": Family.SEVEN,
        "8": Family.EIGHT_SE,
        "se2": Family.EIGHT_SE,
        "se3": Family.EIGHT_SE,
        "8/se2/se3": Family.EIGHT_SE,
        "face": Family.FACE_ID,
        "faceid": Family.FACE_ID,
        "x": Family.FACE_ID,
        "x-15": Family.FACE_ID,
        "x–15": Family.FACE_ID,
    }
    key = choice.strip().lower()
    return mapping.get(key, Family.FACE_ID)
