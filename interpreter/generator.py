from interpreter.debug import currentLoop


class Generator:
    def __init__(self, loop):
        self.loop = loop
        self.loop.end = self.end

    def end(self, value):
        # when instruction RETURN_CONST or RETURN_VALUE is called, raise a stopIteration
        raise StopIteration

    def __iter__(self):
        return self

    def send(self, value):
        with currentLoop(self.loop):
            self.loop.stack.append(value)
            return self.loop.run()

    def __next__(self):
        return self.send(None)
