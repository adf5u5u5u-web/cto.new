import os
import sys
import time
import platform
import logging
from datetime import datetime
from typing import Optional


LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs")


def is_macos() -> bool:
    return platform.system() == "Darwin"


def ensure_log_dir() -> str:
    os.makedirs(LOG_DIR, exist_ok=True)
    return LOG_DIR


def make_log_path(prefix: str = "dfu") -> str:
    ensure_log_dir()
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    return os.path.join(LOG_DIR, f"{prefix}_{ts}.log")


_logger: Optional[logging.Logger] = None


def get_logger() -> logging.Logger:
    global _logger
    if _logger is not None:
        return _logger

    log_path = make_log_path("dfu")
    logger = logging.getLogger("dfu_guide")
    logger.setLevel(logging.INFO)

    # File handler
    fh = logging.FileHandler(log_path)
    fh.setLevel(logging.INFO)
    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    fh.setFormatter(formatter)
    logger.addHandler(fh)

    # Console handler (stderr)
    ch = logging.StreamHandler(stream=sys.stderr)
    ch.setLevel(logging.WARNING)
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    logger.info("Logger initialized. Log file: %s", log_path)
    _logger = logger
    return logger


def human_interval(seconds: float) -> str:
    return f"{seconds:.2f}s"


def sleep(seconds: float) -> None:
    time.sleep(seconds)
