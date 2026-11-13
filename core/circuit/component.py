# BaseComponent (node)
from port import InputPort, OutputPort


class BaseComponent:
    def __init__(self):
        self.inputs: list[InputPort] = []
        self.outputs: list[OutputPort] = []

    def evaluate(self, frame: int, time: float):
        """Compute outputs from inputs. Override in subclasses."""
        ...
