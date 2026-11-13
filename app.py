from managers.tool_manager import ToolManager
from managers.timeline_manager import TimelineManager
from managers.circuit_manager import CircuitManager
from managers.layer_manager import LayerManager
from managers.input_manager import InputManager
from managers.undo_manager import UndoManager
from managers.save_manager import SaveManager
from managers.export_manager import ExportManager
from managers.preferences_manager import PreferencesManager
from ui.main_window import MainWindow


class App:
    def __init__(self):
        self.logging = True
        if (self.logging):
            print("PreferencesManager()...")
        self.preferences_manager = PreferencesManager(self)
        if (self.logging):
            print("ToolManager()...")
        self.tool_manager = ToolManager(self)
        if (self.logging):
            print("TimelineManager()...")
        self.timeline_manager = TimelineManager(self)
        if (self.logging):
            print("CircuitManager()...")
        self.circuit_manager = CircuitManager(self)
        if (self.logging):
            print("LayerManager()...")
        self.layer_manager = LayerManager(self)
        if (self.logging):
            print("InputManager()...")
        self.input_manager = InputManager(self)
        if (self.logging):
            print("UndoManager()...")
        self.undo_manager = UndoManager(self)
        if (self.logging):
            print("SaveManager()...")
        self.save_manager = SaveManager(self)
        if (self.logging):
            print("ExportManager()...")
        self.export_manager = ExportManager(self)
        if (self.logging):
            print("MainWindow()...")
        self.main_window = MainWindow(self)
        if (self.logging):
            print("timeline_manager.init_interpolation_modes...")
        self.timeline_manager.init_interpolation_modes()
        if (self.logging):
            print("tool_manager.init()...")
        self.tool_manager.init()
        if (self.logging):
            print("App fully initialized!")
