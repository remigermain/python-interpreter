from interpreter.stack import Stack
from interpreter.generator import Generator
from interpreter.operators import OPERATORS
import time
from collections import deque
import logging
import dis


class ExecutionLoop:
    def __init__(
        self,
        insts,
        pointer=0,
        name=None,
        co_names=None,
        co_consts=None,
        co_varnames=None,
    ):
        self.insts = list(reversed(list(insts)))
        self.pointer = len(self.insts) - 1
        self.stack = Stack()
        self.name = name or "NO-SET"

        self.co_builtins = __builtins__
        self.co_globals = {"time": time}
        self.co_locals = {}
        self.co_names = dict(co_names or {})

        self.co_consts = list(co_consts or [])
        self.co_varnames = {key: value for key, value in enumerate(co_varnames or [])}

        self.logger = logging.getLogger(name or "Runner")

        # TODO: remove this shit
        self._co_kw = deque(maxlen=1)

        self.sub_loop = None

    def end(self, value):
        return value

    def jump_forward(self, inst, padding):
        offest = (inst.arg * 2) + padding + inst.offset
        while self.insts[self.pointer].offset < offest:
            self.pointer -= 1

    def jump_backward(self, inst, padding):
        offest = inst.offset - (inst.arg * 2 - padding)
        self.pointer += 1
        while self.insts[self.pointer].offset > offest:
            self.pointer += 1

    def critical(self):
        if self.sub_loop:
            self.sub_loop.critical()

        self.logger.critical(f"Loop[{self.name}]")
        self.logger.critical(f"\tpointer: {len(self.insts) - self.pointer}")
        self.logger.critical(f"\topname: {self.inst.opname}")
        self.logger.critical(f"\tinst: {self.inst}")
        self.logger.critical(f"\tstack: {self.stack}")
        self.logger.critical(f"\tco_globals: {self.co_globals}")
        self.logger.critical(f"\tco_locals: {self.co_locals}")
        self.logger.critical(f"\tco_names: {self.co_names}")
        self.logger.critical(f"\tco_consts: {self.co_consts}")
        self.logger.critical(f"\tco_varnames: {self.co_varnames}")

    def run(self):
        while self.pointer >= 0:
            self.inst = self.insts[self.pointer]
            self.pointer -= 1

            self.logger.debug(f"{self.inst=}")

            match self.inst.opname:
                case "POP_TOP":
                    self.stack.pop()
                case "COPY":
                    self.stack.append(self.stack[-self.inst.arg])

                case "NOP" | "RESUME" | "PUSH_NULL":
                    pass

                case "RETURN_VALUE":
                    return self.end(self.stack.pop())

                case "RETURN_CONST":
                    # return self.end(self.co_consts[inst.arg])
                    return self.end(self.inst.argval)

                case "BUILD_LIST":
                    count = self.inst.arg
                    self.stack, values = self.stack[:-count], self.stack[-count:]
                    self.stack.append(list(values))
                case "BUILD_TUPLE":
                    count = self.inst.arg
                    self.stack, values = self.stack[:-count], self.stack[-count:]
                    self.stack.append(tuple(values))

                # -----
                # store function
                # -----
                case "STORE_FAST":
                    self.co_varnames[self.inst.arg] = self.stack.pop()

                case "STORE_GLOBAL":
                    self.co_globals[self.inst.argval] = self.stack.pop()

                case "STORE_NAME":
                    self.co_names[self.inst.argval] = self.stack.pop()

                # -----
                # load function
                # -----
                case "LOAD_CONST":
                    self.stack.append(self.inst.argval)

                case "LOAD_FAST":
                    self.stack.append(self.co_varnames[self.inst.arg])

                case "LOAD_GLOBAL":
                    for store in (
                        self.co_globals,
                        self.co_builtins,
                    ):
                        if self.inst.argval in store:
                            self.stack.append(store[self.inst.argval])
                            break
                    else:
                        raise Exception(f"Can't find {self.inst.argval!r}")

                case "LOAD_NAME":
                    for store in (
                        self.co_names,
                        self.co_locals,
                        self.co_globals,
                        self.co_builtins,
                    ):
                        if self.inst.argval in store:
                            self.stack.append(store[self.inst.argval])
                            break
                    else:
                        raise Exception(f"Can't find {self.inst.argval!r}")

                case "LOAD_ATTR":
                    attr = getattr(self.stack.pop(), self.inst.argval)
                    self.stack.append(attr)

                # -----
                # function functions
                # -----
                case "MAKE_FUNCTION":
                    bytescode = self.stack.pop()

                    def caller(*ar, **kw):
                        b = ExecutionLoop(
                            dis.Bytecode(bytescode),
                            co_varnames=[*ar, *list(kw.values())],
                            name=self.insts[self.pointer].argval,
                        )
                        self.sub_loop = b
                        res = b.run()
                        self.sub_loop = None
                        return res

                    self.stack.append(caller)

                case "CALL":
                    args = []
                    kw = {}
                    arguements_length = self.inst.argval
                    if self._co_kw:
                        for k in reversed(self._co_kw.pop()):
                            kw[k] = self.stack.pop()
                            arguements_length -= 1

                    # args
                    for _ in range(arguements_length):
                        args.append(self.stack.pop())
                    args = list(reversed(args))

                    caller = self.stack.pop()

                    # TODO remove this shit again
                    if caller:
                        result = caller(*args, **kw)
                    else:
                        result = None

                    self.stack.append(result)

                case "KW_NAMES":
                    self._co_kw.append(self.inst.argval)

                # -----
                # conditions instructions
                # -----
                case "POP_JUMP_IF_TRUE":
                    if self.stack.pop() is not True:
                        self.jump_forward(self.inst, 2)

                case "POP_JUMP_IF_FALSE":
                    if self.stack.pop() is not False:
                        self.jump_forward(self.inst, 2)

                case "POP_JUMP_IF_NOT_NONE":
                    if self.stack.pop() is not None:
                        self.jump_forward(self.inst, 2)

                # -----
                # Jump instructions
                # -----
                case "JUMP_FORWARD":
                    self.jump_forward(self.inst, 2)

                case "JUMP_BACKWARD":
                    self.jump_backward(self.inst, 2)

                # -----
                # operator instructions
                # -----
                case "UNPACK_SEQUENCE":
                    self.stack.extend(self.stack.pop()[: -self.inst.arg - 1 : -1])

                case "IS_OP":
                    second, first = self.stack.pop(), self.stack.pop()
                    if self.inst.arg == 1:
                        self.stack.append(first is not second)
                    else:
                        self.stack.append(first is second)

                case "CONTAINS_OP":
                    second, first = self.stack.pop(), self.stack.pop()
                    if self.inst.arg == 1:
                        self.stack.append(first not in second)
                    else:
                        self.stack.append(first in second)

                case "COMPARE_OP":
                    second, first = self.stack.pop(), self.stack.pop()
                    COMPARE = {
                        2: lambda: first < last,
                        40: lambda: first == last,
                        92: lambda: first >= last,
                    }
                    if self.inst.arg not in COMPARE:
                        self.logger.error(
                            f"Invalid COMPARE_OP {self.inst.arg!r} {self.inst.argrepr!r}"
                        )
                        continue
                    self.stack.append(COMPARE[self.inst.arg]())

                case "BINARY_OP":
                    second, first = self.stack.pop(), self.stack.pop()
                    if self.inst.arg not in OPERATORS:
                        self.logger.error(
                            f"Invalid BINARY_OP {self.inst.arg!r} {self.inst.argrepr!r}"
                        )
                        continue
                    self.stack.append(OPERATORS[self.inst.arg](first, second))

                # -----
                # iter instructions
                # -----
                case "GET_ITER":
                    self.stack[-1] = iter(self.stack[-1])

                case "FOR_ITER":
                    iterator = self.stack[-1]
                    try:
                        self.stack.append(next(iterator))
                    except StopIteration:
                        self.jump_forward(self.inst, 4)
                        self.stack.append(None)

                case "END_FOR":
                    self.stack.pop()
                    self.stack.pop()

                case "RETURN_GENERATOR":
                    return Generator(self)

                case "YIELD_VALUE":
                    return self.stack.pop()

                # -----
                # contextmanager instructions
                # -----
                case "BEFORE_WITH":
                    last = self.stack.pop()
                    # push exit for the WITH_EXCEPT_START instruction
                    self.stack.append(last.__exit__)
                    self.stack.append(last.__enter__())

                case _:
                    self.logger.warning(
                        "Instruction %r not implemented...", self.inst.opname
                    )

        return self.end(self.stack.pop())
