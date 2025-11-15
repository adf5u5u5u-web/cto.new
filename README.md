# DFU Guide (macOS)

A Python 3.11+ tool to help guide iPhones into DFU mode on macOS. Provides both a CLI and a simple Tkinter GUI. The CLI/GUI share the same core logic for device state detection and per-model DFU timing guidance.

Features
- Device detection via system_profiler (SPUSBDataType) and ioreg -p IOUSB
- Polling at configurable interval (default 500ms)
- Model family selection with per-second guidance and audio/voice prompts
- Logging of state transitions and matched USB entries to logs/dfu_YYYYMMDD_HHMMSS.log
- CLI with exit codes: 0=DFU, 2=Recovery, 1/other=Failed/Unknown
- Tkinter GUI using non-blocking after() timers

Supported families
- 6s (and earlier, Home button)
- 7 / 7 Plus
- 8 / SE2 / SE3 (pre-Face ID button layout)
- Face ID series (X/XS/11/12/13/14/15)

Usage
- CLI (default):
  python -m dfu_guide --mode cli --family 8 --beep on --voice off --interval 0.5

- GUI:
  python -m dfu_guide --mode gui

Notes
- On non-macOS platforms, detection and audio are no-ops. Parsing utilities are still available and tested.
- Audio prompts (beep/voice) require macOS utilities: afplay and osascript.

Development
- Python 3.11+
- No external dependencies required
- Run unit tests with your preferred test runner

Limitations
- Actual DFU transitions can vary by exact device and state; follow on-screen prompts.
- GUI and CLI are minimal by design. More advanced features are possible as future work.
