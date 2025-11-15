import argparse
import signal
import sys
import threading
import time

from .audio import AudioFeedback
from .detector import Detector, Mode
from .guide import FAMILY_CHOICES, GuideRunner, family_from_choice
from .utils import get_logger, readable_mode_name


logger = get_logger()


def _watch(args):
    stop = threading.Event()

    def on_change(res):
        logger.info(f"当前状态: {readable_mode_name(res.mode)} (via {res.source})")

    det = Detector(interval=args.interval, on_change=on_change)

    def handle_sigint(sig, frame):
        stop.set()

    signal.signal(signal.SIGINT, handle_sigint)
    det.start()
    logger.info("开始监控，按 Ctrl+C 退出…")
    try:
        while not stop.is_set():
            time.sleep(0.2)
    finally:
        det.stop()


def _guide(args):
    det = Detector(interval=args.interval)
    audio = AudioFeedback(beep_enabled=not args.no_beep, voice_enabled=args.voice)
    runner = GuideRunner(
        detector=det,
        audio=audio,
        on_tick=lambda sec, label: print(f"\r[{label}] 倒计时: {sec:02d}s   ", end="", flush=True),
        on_step=lambda step: print(f"\n>> {step.title}", flush=True),
        on_finish=lambda ok, msg: print(f"\n{msg}")
    )

    det.start()
    logger.info(f"机型族: {args.family}")
    logger.info("按提示操作。如需退出，按 Ctrl+C。\n")
    try:
        runner.start(family_from_choice(args.family))
        # Wait until guide thread ends
        while runner._thread and runner._thread.is_alive():
            time.sleep(0.2)
    except KeyboardInterrupt:
        print("\n手动中止。")
    finally:
        runner.stop()
        det.stop()


def build_parser():
    parser = argparse.ArgumentParser(
        prog="dfu-guide",
        description="iPhone DFU 引导工具（CLI）"
    )
    sub = parser.add_subparsers(dest="cmd")

    p_watch = sub.add_parser("watch", help="实时监控 DFU/恢复/正常 状态")
    p_watch.add_argument("--interval", type=float, default=0.5, help="轮询间隔（秒）")
    p_watch.set_defaults(func=_watch)

    p_guide = sub.add_parser("guide", help="开始按机型族的 DFU 引导")
    p_guide.add_argument("--family", default="face", help=f"机型族（可选：home/7/8/se2/se3/face），默认 face")
    p_guide.add_argument("--voice", action="store_true", help="开启语音提示（需 macOS）")
    p_guide.add_argument("--no-beep", action="store_true", help="关闭蜂鸣提示")
    p_guide.add_argument("--interval", type=float, default=0.5, help="检测轮询间隔（秒）")
    p_guide.set_defaults(func=_guide)

    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)

    if not hasattr(args, "func"):
        parser.print_help()
        return 1
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
