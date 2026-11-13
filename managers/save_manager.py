from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from app import App


class SaveManager:
    def __init__(self, app: "App"):
        self.app = app

    def onNewProject(self):
        print("SaveManager: New project")

    def onOpenProject(self):
        print("SaveManager: Open project")

    def onSave(self):
        print("SaveManager: Save project")
