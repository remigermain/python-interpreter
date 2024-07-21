import os
import time
from functools import partial


def _format_dict(dtc, name):
    if not dtc:
        print(f"{name}: {'{}'}")
        return

    print(f"{name}: {'{'}")
    for k, v in dtc.items():
        print(f"\t{k}: {v!r},")
    print("}")


def _format_list(lst, name):
    if not lst:
        print(f"{name}: []")
        return

    print(f"{name}: [")
    for v in lst:
        print(f"\t{v!r},")
    print("]")


def debug_visual(loop, step=None):
    if isinstance(loop, (int, float, str)):
        return partial(debug_visual, step=loop)

    os.system("clear")

    print(f"Loop[{loop.name}]")
    print(f"pointer: {loop.pointer}")
    print(f"instruction: {loop.inst.opname}")

    _format_list(reversed(loop.stack), "Stack")
    _format_dict(loop.co_globals, "CoGlobals")
    _format_dict(loop.co_locals, "CoLocals")
    _format_dict(loop.co_names, "CoNames")
    _format_list(loop.co_consts, "CoConst")
    _format_dict(loop.co_varnames, "CoVarnames")

    if isinstance(step, str):
        input()
    else:
        time.sleep(step)


def critical_logger(loop):
    loop.logger.critical(f"Loop[{loop.name}]")
    loop.logger.critical(f"\tpointer: {len(loop.insts) - loop.pointer}")
    loop.logger.critical(f"\topname: {loop.inst.opname}")
    loop.logger.critical(f"\tinst: {loop.inst}")
    loop.logger.critical(f"\tstack: {loop.stack}")
    loop.logger.critical(f"\tco_globals: {loop.co_globals}")
    loop.logger.critical(f"\tco_locals: {loop.co_locals}")
    loop.logger.critical(f"\tco_names: {loop.co_names}")
    loop.logger.critical(f"\tco_consts: {loop.co_consts}")
    loop.logger.critical(f"\tco_varnames: {loop.co_varnames}\n")


_current_loop = []


class currentLoop:
    def __init__(self, loop):
        self._loop = loop

    def __enter__(self):
        _current_loop.append(self._loop)

    def __exit__(self, exec_t, exec_v, exec_tb):
        if exec_v:
            raise
        global _current_loop
        del _current_loop[-1]

    @staticmethod
    def get():
        return _current_loop[-1]

    @staticmethod
    def getAll():
        return _current_loop
