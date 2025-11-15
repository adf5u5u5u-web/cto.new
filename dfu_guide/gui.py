from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from .audio import beep, say
from .detector import DeviceState, DetectResult, Detector
from .guide import FAMILIES, get_schedule
from .utils import get_logger


class App:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.logger = get_logger()
        self.root.title("DFU Guide (macOS)")
        self.root.geometry("520x320")

        self.family_var = tk.StringVar(value="8")
        self.beep_var = tk.BooleanVar(value=True)
        self.voice_var = tk.BooleanVar(value=False)
        self.status_var = tk.StringVar(value="Device state: UNKNOWN")
        self.countdown_var = tk.StringVar(value="Idle")

        frm = ttk.Frame(root, padding=12)
        frm.pack(fill=tk.BOTH, expand=True)

        row = 0
        ttk.Label(frm, text="Model family:").grid(row=row, column=0, sticky=tk.W)
        self.family_cb = ttk.Combobox(frm, textvariable=self.family_var, values=list(FAMILIES.keys()), state="readonly", width=12)
        self.family_cb.grid(row=row, column=1, sticky=tk.W)

        row += 1
        self.beep_cb = ttk.Checkbutton(frm, text="Beep", variable=self.beep_var)
        self.beep_cb.grid(row=row, column=0, sticky=tk.W)
        self.voice_cb = ttk.Checkbutton(frm, text="Voice", variable=self.voice_var)
        self.voice_cb.grid(row=row, column=1, sticky=tk.W)

        row += 1
        self.start_btn = ttk.Button(frm, text="Start", command=self.on_start)
        self.start_btn.grid(row=row, column=0, pady=8)
        self.stop_btn = ttk.Button(frm, text="Stop", command=self.on_stop, state=tk.DISABLED)
        self.stop_btn.grid(row=row, column=1, pady=8)

        row += 1
        ttk.Label(frm, textvariable=self.status_var, font=("Helvetica", 12)).grid(row=row, column=0, columnspan=2, sticky=tk.W, pady=8)

        row += 1
        self.count_label = ttk.Label(frm, textvariable=self.countdown_var, font=("Helvetica", 18, "bold"))
        self.count_label.grid(row=row, column=0, columnspan=2, sticky=tk.W)

        # Detector
        self.detector = Detector(interval=0.5, callback=self.on_detect)
        self.detector.start()

        # Guide
        self._guide_running = False
        self._guide_schedule = []
        self._guide_idx = 0
        self._guide_remaining = 0

        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def on_detect(self, res: DetectResult) -> None:
        self.status_var.set(f"Device state: {res.state.name}")
        if res.state == DeviceState.DFU:
            self.countdown_var.set("DFU detected! Release buttons. To exit DFU: Volume Up, Volume Down, hold Side.")
            if self.beep_var.get():
                beep()
            if self.voice_var.get():
                say("DFU mode detected")
        elif res.state == DeviceState.RECOVERY:
            self.countdown_var.set("Recovery mode detected. Try again, release timing is critical.")

    def on_start(self) -> None:
        if self._guide_running:
            return
        family = self.family_var.get().strip().lower()
        self._guide_schedule = get_schedule(family)
        self._guide_idx = 0
        self._guide_remaining = self._guide_schedule[0].duration if self._guide_schedule else 0
        self._guide_running = True
        self.start_btn.configure(state=tk.DISABLED)
        self.stop_btn.configure(state=tk.NORMAL)
        self.countdown_var.set("Starting guide...")
        self.root.after(500, self._tick)

    def on_stop(self) -> None:
        self._guide_running = False
        self.start_btn.configure(state=tk.NORMAL)
        self.stop_btn.configure(state=tk.DISABLED)
        self.countdown_var.set("Stopped.")

    def _tick(self) -> None:
        if not self._guide_running or not self._guide_schedule:
            return
        step = self._guide_schedule[self._guide_idx]
        if self._guide_remaining <= 0:
            # Step transition
            self._guide_idx += 1
            if self._guide_idx >= len(self._guide_schedule):
                self.countdown_var.set("Guide finished. Await device DFU detection.")
                self.on_stop()
                return
            step = self._guide_schedule[self._guide_idx]
            self._guide_remaining = step.duration
            if self.voice_var.get():
                say(step.instruction)
        # Tick
        self.countdown_var.set(f"{step.instruction} | {self._guide_remaining}s")
        if self.beep_var.get():
            beep()
        self._guide_remaining -= 1
        self.root.after(1000, self._tick)

    def on_close(self) -> None:
        try:
            self.detector.stop()
        except Exception:
            pass
        self.root.destroy()


def run() -> int:
    root = tk.Tk()
    App(root)
    root.mainloop()
    return 0
