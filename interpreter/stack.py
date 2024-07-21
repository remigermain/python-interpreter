from functools import cache


class Stack(list):
    def pop(self):
        try:
            return super().pop()
        except IndexError:
            return None


@cache
class _Null:
    def __repr__(self):
        return "NULL"


NULL = _Null()
