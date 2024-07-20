OPERATORS = {
    0: lambda a, b: a + b,
    1: lambda a, b: a & b,
    2: lambda a, b: a // b,
    4: lambda a, b: a @ b,
    5: lambda a, b: a * b,
    6: lambda a, b: a % b,
    7: lambda a, b: a | b,
    8: lambda a, b: a**b,
    10: lambda a, b: a - b,
    12: lambda a, b: a ^ b,
}
# all self operator (iadd, isub, ...ect)
# is operator code + 13
for code, func in list(OPERATORS.items()):
    OPERATORS[code + 13] = func
