from enum import UNIQUE, IntEnum, auto, verify


@verify(UNIQUE)
class INSTRUCTION(IntEnum):
    LESS = 2
    LESS_EQUAL = 26
    EQUAL = 40
    NOT_EQUAL = 55
    UPPER = 68
    UPPER_EQUAL = 92


COMPARES = {
    INSTRUCTION.LESS: lambda a, b: a < b,
    INSTRUCTION.LESS_EQUAL: lambda a, b: a <= b,
    INSTRUCTION.UPPER: lambda a, b: a > b,
    INSTRUCTION.UPPER_EQUAL: lambda a, b: a >= b,
    INSTRUCTION.EQUAL: lambda a, b: a == b,
    INSTRUCTION.NOT_EQUAL: lambda a, b: a != b,
}
