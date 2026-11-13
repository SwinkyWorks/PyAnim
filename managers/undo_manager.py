from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from app import App


class UndoRecord:
    def __init__(self):
        pass


class UndoManager:
    def __init__(self, app: "App"):
        self.app = app
        self.records: list[UndoRecord] = []

    def push(self, record: UndoRecord):
        self.records.append(record)
