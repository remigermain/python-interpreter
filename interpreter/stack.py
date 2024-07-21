from functools import cache


class Stack(list):
    def __init__(self, *ar, **kw):
        super().__init__(*ar, **kw)
        self.pointer = len(self) - 1

    def jump_forward(self, padding):
        offest = (self.actual.arg * 2) + padding + self.actual.offset
        while self[self.pointer].offset < offest:
            self.pointer -= 1

    def jump_backward(self, padding):
        offest = self.actual.offset - (self.actual.arg * 2 - padding)
        self.pointer += 1
        while self[self.pointer].offset > offest:
            self.pointer += 1

    def next(self):
        self.actual = self[self.pointer]
        self.pointer -= 1
        return self.actual

    @property
    def next_inst(self):
        return self[self.pointer]

    def pop(self):
        try:
            return super().pop()
        except IndexError:
            return None

    def __bool__(self):
        return self.pointer >= 0


@cache
class _Null:
    def __repr__(self):
        return "NULL"


NULL = _Null()
