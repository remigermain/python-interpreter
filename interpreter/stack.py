class Stack(list):
    def last(self):
        return self[-1]

    def set_last(self, el):
        self[-1] = el

    def pop(self):
        try:
            return super().pop()
        except IndexError:
            return None
