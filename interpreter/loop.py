import dis
import logging
import time
from collections import defaultdict, deque

from interpreter.compare import COMPARES
from interpreter.debug import currentLoop
from interpreter.generator import Generator
from interpreter.operators import OPERATORS
from interpreter.stack import Stack


class ExecutionLoop:
    def __init__(self, insts, name=None, co_names=None, co_consts=None, co_varnames=None, notify=None):
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

        self.logger = logging.getLogger(name or "")

        # TODO: remove this shit
        self._co_kw = deque(maxlen=1)

        self._notify = defaultdict(set)
        self._notify.update(notify or {})

    def __repr__(self):
        return f"<ExecutionLoop name={self.name}>"

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

    def on_notify(self, action, func):
        self._notify[action].add(func)

    def notify(self, action):
        for action in self._notify[action]:
            action(self)

    def run(self):
        while self.pointer >= 0:
            self.inst = self.insts[self.pointer]
            self.pointer -= 1

            self.notify("INSTRUCTION")

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
                    for store in (self.co_globals, self.co_builtins):
                        if self.inst.argval in store:
                            self.stack.append(store[self.inst.argval])
                            break
                    else:
                        raise Exception(f"Can't find {self.inst.argval!r}")

                case "LOAD_NAME":
                    for store in (self.co_names, self.co_locals, self.co_globals, self.co_builtins):
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
                    name = "Function: " + self.insts[self.pointer].argval
                    def caller(*ar, **kw):
                        b = ExecutionLoop(
                            dis.Bytecode(bytescode),
                            co_varnames=[*ar, *list(kw.values())],
                            name=name,
                            notify=self._notify
                        )
                        with currentLoop(b):
                            return b.run()

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
                    if self.stack.pop() is True:
                        self.jump_forward(self.inst, 2)

                case "POP_JUMP_IF_FALSE":
                    if self.stack.pop() is False:
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
                    self.stack.append(COMPARES[self.inst.arg](first, second))

                case "BINARY_OP":
                    second, first = self.stack.pop(), self.stack.pop()
                    self.stack.append(OPERATORS[self.inst.arg](first, second))

                case "UNARY_NOT":
                    self.stack[-1] = not self.stack[-1]

                case "UNARY_NEGATIVE":
                    self.stack[-1] = -self.stack[-1]

                case "UNARY_INVERT":
                    self.stack[-1] = ~self.stack[-1]

                case "GET_LEN":
                    self.stack.append(len(self.stack[-1]))

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
                    self.logger.warning("Instruction %r not implemented...", self.inst.opname)

        return self.end(self.stack.pop())
