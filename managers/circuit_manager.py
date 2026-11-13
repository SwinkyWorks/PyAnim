from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from app import App


class CircuitManager:
    def __init__(self, app: "App"):
        self.app = app

    def resolve(self, frame: int, time: float):
        pass
