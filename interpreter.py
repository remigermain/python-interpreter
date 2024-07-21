import argparse
import dis
import logging
import sys

from interpreter.debug import critical_logger, currentLoop, debug_visual
from interpreter.loop import ExecutionLoop


def main():
    parser = argparse.ArgumentParser(
        prog="python-interpreter",
        description="a python bytes code interpreter coded in python",
    )
    parser.add_argument("file", help="file to execute")
    parser.add_argument(
        "-o",
        help="generator ouput bytes code in output.txt",
        action="store_true",
        default=True,
    )
    parser.add_argument(
        "--level",
        help="level of logging",
        default=logging.WARNING,
        choices=logging.getLevelNamesMapping(),
    )
    parser.add_argument("--debug", help="show instructions debugs", action="store_true", default=False)
    flags = parser.parse_args()

    with open(flags.file) as f:
        content = f.read()

    if flags.o:
        with open("output.txt", "w") as f:
            dis.dis(content, file=f)
    if not flags.debug:
        logging.basicConfig(stream=sys.stdout, level=flags.level)
    
    loop = ExecutionLoop(dis.Bytecode(content), name="MainLoop")

    if flags.debug:
        loop.on_notify("INSTRUCTION", debug_visual)
    try:
        with currentLoop(loop):
            loop.run()
    except Exception:
        critical_logger(loop)
        # raise


if __name__ == "__main__":
    main()
