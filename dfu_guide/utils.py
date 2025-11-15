import logging
import os
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Tuple


_LOGGER: Optional[logging.Logger] = None


def project_root() -> Path:
    # This file is dfu_guide/utils.py => parent is dfu_guide, parent.parent is repo root
    return Path(__file__).resolve().parent.parent


def logs_dir() -> Path:
    d = project_root() / "logs"
    d.mkdir(parents=True, exist_ok=True)
    return d


def get_log_file_path() -> Path:
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    return logs_dir() / f"dfu_{ts}.log"


def get_logger() -> logging.Logger:
    global _LOGGER
    if _LOGGER is not None:
        return _LOGGER

    logger = logging.getLogger("dfu_guide")
    logger.setLevel(logging.INFO)

    # Avoid duplicate handlers when re-imported
    if not logger.handlers:
        # File handler
        try:
            fh = logging.FileHandler(get_log_file_path(), encoding="utf-8")
            fh.setLevel(logging.INFO)
            fh.setFormatter(
                logging.Formatter(
                    fmt="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
                    datefmt="%Y-%m-%d %H:%M:%S",
                )
            )
            logger.addHandler(fh)
        except Exception:
            # Fallback to not crashing if file cannot be created
            pass

        # Console handler
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)
        ch.setFormatter(
            logging.Formatter(fmt="%(message)s")
        )
        logger.addHandler(ch)

    _LOGGER = logger
    return logger


def is_macos() -> bool:
    return sys.platform == "darwin"


def which(cmd: str) -> Optional[str]:
    return shutil.which(cmd)


def run_cmd(command: List[str], timeout: float = 5.0) -> Tuple[int, str, str]:
    try:
        proc = subprocess.run(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=timeout,
            check=False,
        )
        return proc.returncode, proc.stdout or "", proc.stderr or ""
    except Exception as e:
        return 1, "", str(e)


def readable_mode_name(mode: str) -> str:
    mapping = {
        "DFU": "DFU 模式",
        "RECOVERY": "恢复模式",
        "NORMAL": "正常模式",
        "DISCONNECTED": "未连接",
        "UNKNOWN": "未知",
    }
    return mapping.get(mode, mode)


def ensure_tk_available() -> Optional[str]:
    # On macOS, Tkinter is usually bundled. We don't import here but let GUI module import it.
    # Return None if OK, else reason string
    try:
        import tkinter  # noqa: F401

        return None
    except Exception as e:
        return str(e)


def env_true(name: str, default: bool = False) -> bool:
    v = os.environ.get(name)
    if v is None:
        return default
    return v.strip().lower() in {"1", "true", "yes", "on"}
