import queue
import threading
import tkinter as tk
from tkinter import ttk

from .audio import AudioFeedback
from .detector import DetectionResult, Detector, Mode
from .guide import FAMILY_CHOICES, Family, GuideRunner
from .utils import ensure_tk_available, get_logger, readable_mode_name


logger = get_logger()


class DFUApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("DFU 引导工具 V2")
        self.root.geometry("640x420")

        self.queue: "queue.Queue[tuple]" = queue.Queue()

        # Detector
        self.detector = Detector(interval=0.5, on_change=self._on_detect_change)
        self.detector.start()

        # Audio
        self.audio = AudioFeedback(beep_enabled=True, voice_enabled=False)

        # Guide Runner
        self.runner = GuideRunner(
            detector=self.detector,
            audio=self.audio,
            on_tick=self._on_tick,
            on_step=self._on_step,
            on_finish=self._on_finish,
        )

        self._build_ui()
        self._schedule_process_queue()

    def _build_ui(self):
        frm = ttk.Frame(self.root, padding=12)
        frm.pack(fill=tk.BOTH, expand=True)

        # Status row
        self.status_var = tk.StringVar(value="当前状态：未知")
        status_label = ttk.Label(frm, textvariable=self.status_var, font=("Helvetica", 12))
        status_label.pack(anchor=tk.W)

        # Family selection
        sel_frame = ttk.Frame(frm)
        sel_frame.pack(fill=tk.X, pady=8)

        ttk.Label(sel_frame, text="机型族：").pack(side=tk.LEFT)
        self.family_var = tk.StringVar(value=Family.FACE_ID.value)
        self.family_box = ttk.Combobox(sel_frame, textvariable=self.family_var, values=FAMILY_CHOICES, state="readonly", width=24)
        self.family_box.pack(side=tk.LEFT, padx=6)

        # Options
        self.voice_var = tk.BooleanVar(value=False)
        self.beep_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(sel_frame, text="语音提示", variable=self.voice_var, command=self._on_voice_toggle).pack(side=tk.LEFT, padx=8)
        ttk.Checkbutton(sel_frame, text="蜂鸣提示", variable=self.beep_var, command=self._on_beep_toggle).pack(side=tk.LEFT)

        # Countdown display
        self.big_var = tk.StringVar(value="准备就绪")
        big = ttk.Label(frm, textvariable=self.big_var, anchor=tk.CENTER)
        big.configure(font=("Menlo", 42, "bold"))
        big.pack(fill=tk.BOTH, expand=True, pady=12)

        # Step/Message
        self.msg_var = tk.StringVar(value="请选择机型族，点击“开始引导”。")
        ttk.Label(frm, textvariable=self.msg_var, font=("Helvetica", 13)).pack(fill=tk.X)

        # Buttons
        btn_frame = ttk.Frame(frm)
        btn_frame.pack(fill=tk.X, pady=8)

        self.start_btn = ttk.Button(btn_frame, text="开始引导", command=self._on_start)
        self.start_btn.pack(side=tk.LEFT)

        self.stop_btn = ttk.Button(btn_frame, text="停止", command=self._on_stop, state=tk.DISABLED)
        self.stop_btn.pack(side=tk.LEFT, padx=8)

    def _on_voice_toggle(self):
        self.audio.voice_enabled = self.voice_var.get()

    def _on_beep_toggle(self):
        self.audio.beep_enabled = self.beep_var.get()

    def _on_start(self):
        self.start_btn.configure(state=tk.DISABLED)
        self.stop_btn.configure(state=tk.NORMAL)
        family = Family(self.family_var.get())
        self.runner.start(family)

    def _on_stop(self):
        self.runner.stop()
        self.start_btn.configure(state=tk.NORMAL)
        self.stop_btn.configure(state=tk.DISABLED)

    def _on_detect_change(self, res: DetectionResult):
        # Thread-safe: put into queue
        self.queue.put(("status", res))

    def _on_tick(self, sec: int, label: str):
        self.queue.put(("tick", sec, label))

    def _on_step(self, step):
        self.queue.put(("step", step))

    def _on_finish(self, ok: bool, msg: str):
        self.queue.put(("finish", ok, msg))

    def _schedule_process_queue(self):
        try:
            while True:
                item = self.queue.get_nowait()
                self._handle_event(item)
        except queue.Empty:
            pass
        finally:
            self.root.after(100, self._schedule_process_queue)

    def _handle_event(self, item: tuple):
        etype = item[0]
        if etype == "status":
            res: DetectionResult = item[1]
            self.status_var.set(f"当前状态：{readable_mode_name(res.mode)}")
            if res.mode == Mode.DFU:
                self.big_var.set("成功进入 DFU！")
                self.msg_var.set("设备已进入 DFU 模式。")
            elif res.mode == Mode.RECOVERY:
                self.msg_var.set("检测到恢复模式：如未成功，请把握松开电源键的时机重试。")
        elif etype == "tick":
            sec, label = item[1], item[2]
            self.big_var.set(f"{sec}")
            self.msg_var.set(label)
        elif etype == "step":
            step = item[1]
            self.msg_var.set(step.title)
        elif etype == "finish":
            ok, msg = item[1], item[2]
            self.msg_var.set(msg)
            # Re-enable start button
            self.start_btn.configure(state=tk.NORMAL)
            self.stop_btn.configure(state=tk.DISABLED)


def main():
    err = ensure_tk_available()
    if err:
        print("Tkinter 不可用：", err)
        return 1
    root = tk.Tk()
    DFUApp(root)
    root.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
