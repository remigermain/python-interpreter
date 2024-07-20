import dis
import argparse
from interpreter.loop import ExecutionLoop
import logging
import sys


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
    flags = parser.parse_args()

    logging.basicConfig(stream=sys.stdout, level=flags.level)

    with open(flags.file) as f:
        content = f.read()

    if flags.o:
        with open("output.txt", "w") as f:
            dis.dis(content, file=f)

    loop = ExecutionLoop(dis.Bytecode(content), name="Main")
    try:
        loop.run()
    except Exception:
        loop.critical()
        raise


if __name__ == "__main__":
    main()
