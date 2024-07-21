class Stack(list):
    def pop(self):
        try:
            return super().pop()
        except IndexError:
            return None
