import argparse
import sys

from . import cli as cli_module
from . import gui as gui_module


def main(argv=None):
    parser = argparse.ArgumentParser(description="DFU 引导工具 V2")
    parser.add_argument("mode", nargs="?", choices=["gui", "cli"], help="运行模式：gui 或 cli")
    args, rest = parser.parse_known_args(argv)

    if args.mode == "cli":
        return cli_module.main(rest)
    # Default to GUI when unspecified
    return gui_module.main()


if __name__ == "__main__":
    sys.exit(main())
