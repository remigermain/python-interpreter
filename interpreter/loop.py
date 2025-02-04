import dis
import inspect
import logging
from collections import defaultdict, deque

from interpreter.compare import COMPARES
from interpreter.debug import currentLoop
from interpreter.generator import Generator
from interpreter.operators import OPERATORS
from interpreter.stack import NULL, Stack


class ExecutionLoop:
    def __init__(
        self,
        insts,
        name=None,
        co_globals=None,
        co_locals=None,
        co_names=None,
        co_consts=None,
        co_varnames=None,
        notify=None,
    ):
        self.stack = Stack(list(reversed(list(insts))))
        self.name = name or "NO-SET"

        self.co_builtins = __builtins__
        self.co_globals = dict(co_globals or {})
        self.co_locals = dict(co_locals or {})
        self.co_names = dict(co_names or {})
        self.co_fastlocalnames = {}
        self.co_consts = list(co_consts or [])
        self.co_varnames = dict(enumerate(co_varnames or []))

        self.logger = logging.getLogger(name or "")

        # TODO: remove this shit
        self._co_kw = deque(maxlen=1)

        self._notify = defaultdict(set)
        self._notify.update(notify or {})

    def __repr__(self):
        return f"<ExecutionLoop name={self.name}>"

    def end(self, value):
        return value

    def on_notify(self, action, func):
        self._notify[action].add(func)

    def notify(self, action):
        for func in self._notify[action]:
            func(self)

    def run(self):
        while self.stack:
            inst = self.stack.next()

            self.notify("INSTRUCTION")

            match inst.opname:
                case "POP_TOP":
                    self.stack.pop()
                case "COPY":
                    self.stack.append(self.stack[-inst.arg])

                case "NOP" | "RESUME":
                    pass

                case "PUSH_NULL":
                    self.stack.append(NULL)

                case "FORMAT_VALUE":
                    formater = ""

                    if (inst.arg & 0x04) == 0x04:
                        formater = self.stack.pop()

                    value = self.stack.pop()
                    if (inst.arg & 0x03) == 0x00:
                        # dont format
                        pass
                    elif (inst.arg & 0x03) == 0x01:
                        value = str(value)
                    elif (inst.arg & 0x03) == 0x02:
                        value = repr(value)
                    elif (inst.arg & 0x03) == 0x03:
                        value = ascii(value)

                    self.stack.append(format(value, formater))

                case "RETURN_VALUE":
                    return self.end(self.stack.pop())

                case "RETURN_CONST":
                    # return self.end(self.co_consts[inst.arg])
                    return self.end(inst.argval)

                # -----
                # store function
                # -----
                case "STORE_FAST":
                    self.co_varnames[inst.arg] = self.stack.pop()

                case "STORE_GLOBAL":
                    self.co_globals[inst.argval] = self.stack.pop()

                case "STORE_NAME":
                    self.co_names[inst.argval] = self.stack.pop()

                case "STORE_SUBSCR":
                    key = self.stack.pop()
                    container = self.stack.pop()
                    value = self.stack.pop()
                    container[key] = value

                case "STORE_SLICE":
                    end = self.stack.pop()
                    start = self.stack.pop()
                    container = self.stack.pop()
                    values = self.stack.pop()
                    container[start:end] = value
                # -----
                # load function
                # -----
                case "LOAD_CONST":
                    self.stack.append(inst.argval)

                case "LOAD_FAST_AND_CLEAR":
                    self.stack.append(self.co_varnames.pop(inst.arg, None))

                case "LOAD_FAST":
                    self.stack.append(self.co_varnames[inst.arg])

                case "LOAD_GLOBAL":
                    for store in (self.co_globals, self.co_builtins):
                        if inst.argval in store:
                            self.stack.append(store[inst.argval])
                            break
                    else:
                        raise Exception(f"Can't find {inst.argval!r}")

                case "LOAD_NAME":
                    for store in (
                        self.co_names,
                        self.co_locals,
                        self.co_globals,
                        self.co_builtins,
                    ):
                        if inst.argval in store:
                            self.stack.append(store[inst.argval])
                            break
                    else:
                        raise Exception(f"Can't find {inst.argval!r}")

                case "LOAD_FROM_DICT_OR_GLOBALS":
                    for store in (self.co_names, self.co_globals, self.co_builtins):
                        if inst.argval in store:
                            self.stack.append(store[inst.argval])
                            break
                    else:
                        raise Exception(f"Can't find {inst.argval!r}")

                case "LOAD_ATTR":
                    attr = getattr(self.stack.pop(), inst.argval)
                    self.stack.append(attr)

                # -----
                # function functions
                # -----
                case "MAKE_FUNCTION":
                    __bytescode = self.stack.pop()
                    __name = ""
                    if self.stack.next_inst.opname == "STORE_NAME":
                        __name = "Function: " + self.stack.next_inst.argval

                    def caller(*ar, __bytescode=__bytescode, __name=__name, **kw):
                        b = ExecutionLoop(
                            dis.Bytecode(__bytescode),
                            co_varnames=[*ar, *list(kw.values())],
                            co_globals={
                                **self.co_globals,
                                **self.co_locals,
                                **self.co_names,
                            },
                            name=__name,
                            notify=self._notify,
                        )
                        with currentLoop(b):
                            return b.run()

                    self.stack.append(caller)

                case "CALL":
                    args = []
                    kw = {}
                    arguements_length = inst.argval
                    if self._co_kw:
                        for k in reversed(self._co_kw.pop()):
                            kw[k] = self.stack.pop()
                            arguements_length -= 1

                    # args
                    for _ in range(arguements_length):
                        args.append(self.stack.pop())
                    args = list(reversed(args))

                    caller = self.stack.pop()

                    need_self = False
                    if self.stack and self.stack[-1] is NULL:
                        need_self = True
                        self.stack.pop()

                    result = caller(*args, **kw)

                    self.stack.append(result)

                case "KW_NAMES":
                    self._co_kw.append(inst.argval)

                # -----
                # conditions instructions
                # -----
                case "POP_JUMP_IF_TRUE":
                    if self.stack.pop() is True:
                        self.stack.jump_forward(2)

                case "POP_JUMP_IF_FALSE":
                    if self.stack.pop() is False:
                        self.stack.jump_forward(2)

                case "POP_JUMP_IF_NOT_NONE":
                    if self.stack.pop() is not None:
                        self.stack.jump_forward(2)

                case "POP_JUMP_IF_NONE":
                    if self.stack.pop() is None:
                        self.stack.jump_forward(2)

                # -----
                # Jump instructions
                # -----
                case "JUMP_FORWARD":
                    self.stack.jump_forward(2)

                case "JUMP_BACKWARD":
                    self.stack.jump_backward(2)

                # -----
                # operator str
                # -----
                case "BUILD_STRING":
                    v = ""
                    for _ in range(inst.arg):
                        v = self.stack.pop() + v
                    self.stack.append(v)

                # -----
                # operator MAP/Dict
                # -----
                case "BUILD_MAP":
                    values = []
                    count = inst.arg
                    if count:
                        values = self.stack[-count:]
                        del self.stack[-count:]
                    self.stack.append(dict(values))

                case "MAP_ADD":
                    value = self.stack.pop()
                    key = self.stack.pop()
                    dtc = self.stack[-inst.arg]
                    dtc[key] = value

                # dict merge not raise error
                case "DICT_MERGE" | "DICT_UPDATE":
                    self.stack[-inst.arg].update(self.stack.pop())

                # -----
                # operator TUPLE
                # -----
                case "BUILD_TUPLE":
                    values = []
                    count = inst.arg
                    if count:
                        values = self.stack[-count:]
                        del self.stack[-count:]
                    self.stack.append(tuple(values))

                # -----
                # operator LIST
                # -----
                case "BUILD_LIST":
                    values = []
                    count = inst.arg
                    if count:
                        values = self.stack[-count:]
                        del self.stack[-count:]
                    self.stack.append(list(values))

                case "LIST_APPEND":
                    item = self.stack.pop()
                    self.stack[-inst.arg].append(item)

                case "LIST_EXTEND":
                    seq = self.stack.pop()
                    self.stack[-inst.arg].extend(seq)

                # -----
                # operator SET
                # -----
                case "BUILD_SET":
                    values = []
                    count = inst.arg
                    if count:
                        self.stack, values = self.stack[:-count], self.stack[-count:]
                    self.stack.append(set(values))

                case "SET_ADD":
                    item = self.stack.pop()
                    self.stack[-inst.arg].add(item)

                case "SET_UPDATE":
                    item = self.stack.pop()
                    self.stack[-inst.arg].update(item)

                # -----
                # operator instructions
                # -----
                case "SWAP":
                    value = self.stack[-inst.arg]
                    lastvalue = self.stack[-1]
                    self.stack[-inst.arg] = lastvalue
                    self.stack[-1] = value

                case "UNPACK_SEQUENCE":
                    self.stack.extend(self.stack.pop()[: -inst.arg - 1 : -1])

                case "IS_OP":
                    second, first = self.stack.pop(), self.stack.pop()
                    if inst.arg == 1:
                        self.stack.append(first is not second)
                    else:
                        self.stack.append(first is second)

                case "CONTAINS_OP":
                    second, first = self.stack.pop(), self.stack.pop()
                    if inst.arg == 1:
                        self.stack.append(first not in second)
                    else:
                        self.stack.append(first in second)

                case "COMPARE_OP":
                    second, first = self.stack.pop(), self.stack.pop()
                    self.stack.append(COMPARES[inst.arg](first, second))

                case "BINARY_OP":
                    second, first = self.stack.pop(), self.stack.pop()
                    self.stack.append(OPERATORS[inst.arg](first, second))

                case "UNARY_NOT":
                    self.stack[-1] = not self.stack[-1]

                case "UNARY_NEGATIVE":
                    self.stack[-1] = -self.stack[-1]

                case "UNARY_INVERT":
                    self.stack[-1] = ~self.stack[-1]

                case "GET_LEN":
                    self.stack.append(len(self.stack[-1]))

                case "BINARY_SUBSCR":
                    key = self.stack.pop()
                    container = self.stack.pop()
                    self.stack.append(container[key])

                case "BINARY_SLICE":
                    end = self.stack.pop()
                    start = self.stack.pop()
                    container = self.stack.pop()
                    self.stack.append(container[start:end])

                # -----
                # delete instructions
                # -----
                case "DELETE_SUBSCR":
                    key = self.stack.pop()
                    container = self.stack.pop()
                    del container[key]

                case "DELETE_NAME":
                    self.co_names.pop(inst.argval, None)

                case "DELETE_GLOBAL":
                    self.co_globals.pop(inst.argval, None)

                case "DELETE_FAST":
                    self.co_varnames.pop(inst.argval, None)

                # -----
                # iter instructions
                # -----
                case "GET_YIELD_FROM_ITER":
                    if all(
                        (
                            not inspect.isgenerator(self.stack[-1]),
                            not inspect.isasyncgen(self.stack[-1]),
                            not inspect.isawaitable(self.stack[-1]),
                        )
                    ):
                        self.stack[-1] = iter(self.stack[-1])

                case "GET_ITER":
                    self.stack[-1] = iter(self.stack[-1])

                case "FOR_ITER":
                    iterator = self.stack[-1]
                    try:
                        self.stack.append(next(iterator))
                    except StopIteration:
                        self.stack.jump_forward(4)
                        self.stack.append(NULL)

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
                    self.stack.extend((last.__exit__, last.__enter__()))

                case "WITH_EXCEPT_START":
                    exec_t = self.stack.pop()
                    exec_v = self.stack.pop()
                    exec_tb = self.stack.pop()

                    context_exit = self.stack.pop()

                    results = context_exit(exec_t, exec_v, exec_tb)

                    self.stack.append(results)

                # -----
                # import
                # -----
                case "IMPORT_NAME":
                    fromlist = self.stack.pop()
                    level = self.stack.pop()
                    module = __import__(
                        inst.argval,
                        globals=self.co_globals,
                        locals=self.co_locals,
                        fromlist=fromlist,
                        level=level,
                    )
                    self.stack.append(module)

                case "IMPORT_FROM":
                    module = self.stack[-1]
                    self.stack.append(getattr(module, inst.argval))

                case _:
                    self.logger.warning(
                        "Instruction %r not implemented...", inst.opname
                    )

        return self.end(self.stack.pop())
