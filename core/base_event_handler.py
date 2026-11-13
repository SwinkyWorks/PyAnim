from typing import Protocol
from PySide6.QtGui import QPainter


class Activatable(Protocol):
    def on_deactivate(self):
        ...

    def on_activate(self):
        ...


class BaseEventHandler:
    def __init__(self, *_) -> None:
        # needed to make sure child `super().__init__()`s call both of us
        super().__init__()
        self.set_properties()

    def set_properties(self):
        """Add properties to `self.properties` to populate the properties pane. `Property` is in your context by default, no need to import."""
        ...

    def on_activate(self):
        """Called when the object is selected."""
        ...

    def on_deactivate(self):
        """Called when the object is deselected."""
        ...

    def on_press(self, x: float, y: float) -> bool | None:
        """Called when the canvas starts clicking while the object is selected.
        \nReturn True to interrupt the selected tool's mouse events."""
        return False

    def on_drag(self, x: float, y: float, dx: float, dy: float) -> bool | None:
        """Called during a canvas drag while the object is selected.
        \nReturn True to interrupt the selected tool's mouse events.
        \nOverrides `on_move`."""
        return False

    def on_move(self, x: float, y: float, dx: float, dy: float) -> bool | None:
        """Called during a canvas move while the object is selected.
        \nReturn True to interrupt the selected tool's mouse events.
        \nDoesn't get called during a drag - use `on_drag` instead."""
        return False

    def on_release(self, x: float, y: float) -> bool | None:
        """Called when the mouse stops clicking while the object is selected.
        \nReturn True to interrupt the selected tool's mouse events."""
        return False

    def on_frame(self, deltaTime: float) -> bool | None:
        """Called every window - not animation - frame while the object is selected.
        \nReturn True to interrupt the selected tool's frame events."""
        # You really shouldn't need an animation frame event.
        # If you do, just remember that nothing in Python can be truly static - including functions.
        # What I'm saying is monkey patch your function into an existing one. It's not that hard.
        return False

    def on_paint(self, painter: QPainter) -> bool | None:
        """Called every canvas paint while the object is selected.
        \nReturn True to interrupt the selected tool's frame events."""
        return False

    def on_key(self, key: str) -> bool | None:
        """Called when a key is pressed while the object is selected. 
        \nReturn True to interrupt all other key events."""
        return False
