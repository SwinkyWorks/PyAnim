# BaseLayer, ShaderLayer
from PySide6.QtGui import QImage, QPainter
from PySide6.QtCore import QSize, QPoint, Qt
from core.base_object import BaseObject
from core.base_plugin import BasePlugin
from typing import TYPE_CHECKING, Self
if TYPE_CHECKING:
    from app import App


class BaseLayer(BaseObject):
    def __init__(self, app: "App", plugin: BasePlugin, name: str | None = None):
        resolved_name = name if name is not None else type(self).__name__ + " " + \
            str(app.layer_manager.get_existing_layers(type(self).__name__))
        super().__init__(app, plugin, resolved_name)
        self.objects: list[BaseObject] = []
        self.children: list[BaseLayer] = []  # empty unless shader
        self.active = True
        self.expanded = True
        self.objects_expanded = True

    def accepts_children(self) -> bool:
        return False  # override in ShaderLayer

    def set_initial_visibility(self):
        """Layers are shown and hidden with `active` rather than per-frame visibility, so they stay visible on every frame."""
        dynamic_value = self.properties["visible"].dynamic_value
        dynamic_value.is_keyframed = False
        dynamic_value.current_value = True

    def render(self, frame: int, time: float) -> QImage:
        """Draw this layer's content. Override in subclasses."""
        ...

    def hit_test(self, x: float, y: float) -> BaseObject | None:
        """Return the object at (x,y), or None. Used by selection tool."""
        ...

    def serialize(self) -> dict: ...
    def deserialize(self, data: dict): ...

    def __repr__(self) -> str:
        return f"{type(self).__name__}(children={self.children},objects={self.objects})"

    def push_undo(self, record):
        self.app.undo_manager.push(record)

    def on_duplicate(self) -> Self | bool:
        layer = super().on_duplicate()
        if (not isinstance(layer, bool)):
            for obj in self.objects:
                o = obj.on_duplicate()
                if not isinstance(o, bool):
                    layer.objects.append(o)
            for lay in self.children:
                l = lay.on_duplicate()
                if not isinstance(l, bool):
                    layer.children.append(l)
            layer.active = self.active
            layer.expanded = self.expanded
        return layer


class ShaderLayer(BaseLayer):
    def accepts_children(self) -> bool:
        return True

    def render(self, frame: int, time: float) -> QImage:
        # 1. Render children (recursive - children may be shaders too)
        child_surfaces = [c.render(frame, time) for c in self.children]
        composited = self._composite_children(child_surfaces)
        # 2. Apply shader effect
        return self.apply_effect(composited)

    def apply_effect(self, surface: QImage) -> QImage:
        """Override to implement the shader."""
        ...

    def _composite_children(self, child_surfaces: list[QImage]) -> QImage:
        new_surface = QImage(
            QSize(self.app.layer_manager.size),
            QImage.Format.Format_RGBA8888
        )
        painter = QPainter()
        new_surface.initPainter(painter)
        for surface in child_surfaces:
            painter.drawImage(QPoint(0, 0), surface)
        painter.end()
        return new_surface
