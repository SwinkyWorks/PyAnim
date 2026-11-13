# InputPort, OutputPort

class InputPort[T]:
    def __init__(self, name: str, default: T):
        self.name = name
        self.connection: OutputPort[T] | None = None  # what's wired in
        self.default = default

    def get_value(self) -> T:
        if self.connection:
            return self.connection.get_value(self)
        return self.default


class OutputPort[T]:
    def __init__(self, name: str):
        self.name = name
        self.value: T

    def get_value(self, other) -> T:
        return self.value
