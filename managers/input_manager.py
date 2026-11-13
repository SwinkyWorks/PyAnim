from core.base_layer import BaseLayer
from core.base_object import BaseObject
from core.base_tool import BaseTool
from core.pyside6_helpers import clear_layout
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app import App
from PySide6.QtWidgets import QWidget, QLayout
from core.base_event_handler import Activatable


class InputManager:
    def __init__(self, app: "App"):
        self.app = app
        self.selected_tool: BaseTool | None = None
        self.selected_object: BaseObject | None = None

    def _select(self, name: str, value: Activatable | None):
        v: Activatable | None = getattr(self, name, None)
        if (v != value):
            if (v != None):
                v.on_deactivate()
            if (value != None):
                value.on_activate()

            setattr(self, name, value)
            self.refresh_properties_pane()

    def select_tool(self, tool: BaseTool | None):
        self._select("selected_tool", tool)

    def select_object(self, obj: BaseObject | None):
        self._select("selected_object", obj)

    def refresh_properties_pane(self):
        widget: QWidget = self.app.main_window.properties_pane
        layout = widget.layout()
        if isinstance(layout, QLayout):
            clear_layout(layout)
            subject = self.selected_object if self.selected_object != None else self.selected_tool
            if subject:
                subject.render_properties_ui(widget)

    def on_canvas_method(self, method_name: str, **kvs):
        result = None
        if self.selected_object != None:
            result = getattr(self.selected_object, "on_" + method_name)(**kvs)
        if not result and self.selected_tool != None:
            getattr(self.selected_tool, "on_" + method_name)(**kvs)

    def delete_selected_object(self):
        selected_object = self.selected_object
        if selected_object != None and not selected_object.on_delete():
            self.selected_object = None

            def search_layer(parent_layer: BaseLayer | None, obj=selected_object):
                object_is_layer = isinstance(obj, BaseLayer)
                layers = parent_layer.children if parent_layer != None else self.app.layer_manager.layers
                if (object_is_layer):
                    for layer in layers:
                        if (obj == layer):
                            layers.remove(obj)
                            return
                elif (parent_layer != None):
                    objects = parent_layer.objects
                    for object in objects:
                        if (obj == object):
                            objects.remove(obj)
                            return
                for layer in layers:
                    search_layer(layer)

            search_layer(None)

            selected_object.deleted = True

            def delete_layer(parent_layer: BaseLayer):
                for object in parent_layer.objects:
                    for prop in object.properties.items():
                        prop.dynamic_value.on_destroy()
                for layer in parent_layer.children:
                    delete_layer(layer)

            if isinstance(selected_object, BaseLayer):
                delete_layer(selected_object)
            else:
                for prop in selected_object.properties.items():
                    prop.dynamic_value.on_destroy()

            del selected_object

            self.selected_object = None
            self.app.layer_manager.update_layers()
            self.app.layer_manager.update_layer_texts()

    def duplicate_selected_object(self):
        if self.selected_object != None and not isinstance(object_copy := self.selected_object.on_duplicate(), bool):
            def search_layer(parent_layer: BaseLayer | None, obj=self.selected_object) -> bool:
                object_is_layer = isinstance(obj, BaseLayer)
                layers = parent_layer.children if parent_layer != None else self.app.layer_manager.layers
                if (object_is_layer and isinstance(object_copy, BaseLayer)):
                    for layer in layers:
                        if (obj == layer):
                            layers.insert(layers.index(obj) + 1, object_copy)
                            return True
                elif (parent_layer != None):
                    objects = parent_layer.objects
                    for object in objects:
                        if (obj == object):
                            objects.insert(objects.index(obj) + 1, object_copy)
                            return True
                return any(search_layer(layer) for layer in layers)

            if (search_layer(None)):
                self.selected_object = object_copy
                self.app.layer_manager.update_layers()
                self.app.layer_manager.update_layer_texts()
