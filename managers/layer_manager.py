from PySide6.QtCore import QSize
from PySide6.QtGui import QImage
from core.base_layer import BaseLayer
from core.base_plugin import BasePlugin
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from app import App


class LayerManager:
    def __init__(self, app: "App", size: QSize = QSize(1280, 720)):
        self.app = app
        self.size = size
        self.layers: list[BaseLayer] = []
        self.registered_layer_types: dict[str,
                                          tuple[BasePlugin, type[BaseLayer]]] = {}
        self.onion_skinning = False
        self.show_all_layers = False
        self.hide_specific_layers: dict[str, bool] = {}

    def register_layer_type(self, plugin: BasePlugin, layer_class: type[BaseLayer]):
        className = layer_class.__name__
        self.registered_layer_types[className] = (plugin, layer_class)

    def create_layer(self, class_name: str):
        cls = self.registered_layer_types[class_name][1]
        if cls is None:
            raise ValueError(f"\"{class_name}\" is not a type!")
        self.layers.append(
            cls(self.app, self.registered_layer_types[class_name][0]))
        self.app.main_window.populate_layers_menu()

    def get_existing_layers(self, class_name: str) -> int:
        cls = self.registered_layer_types[class_name]
        if cls is None:
            return 0
        return len([x for x in self.layers if type(x) == cls])

    def get_layer(self, class_name: str, create_if_none_found: bool = False) -> BaseLayer | None:
        cls = self.registered_layer_types[class_name][1]
        if cls is None:
            return None
        if isinstance(self.app.input_manager.selected_object, cls):
            return self.app.input_manager.selected_object
        for layer in self.layers:
            if isinstance(layer, cls):
                return layer
        if (create_if_none_found):
            _ = cls(self.app, self.registered_layer_types[class_name][0])
            self.layers.append(_)
            self.app.main_window.populate_layers_menu()
            return _
        return

    def composite(self, frame: int, time: float) -> list[QImage]:
        """"""
        new_list: list[QImage] = []
        for layer in self.layers:
            layer_is_in_hide_specific_layers = False
            for key, value in self.hide_specific_layers:
                if (self.registered_layer_types[key] == type(layer) and value):
                    layer_is_in_hide_specific_layers = True
            if (layer.active and not layer_is_in_hide_specific_layers) or self.show_all_layers:
                new_list.append(layer.render(frame, time))
        return new_list

    def _toggle_value(self, name: str):
        setattr(self, name, (v := not getattr(self, name)))
        print(f"LayerManager: {name} is now {v}")
        self.update_layers()

    def toggle_onion_skinning(self):
        """Shows previous and next layers in transparent blue/orange, respectively."""
        self._toggle_value("onion_skinning")

    def toggle_show_all_layers(self):
        """Makes any invisible layers temporarily visible."""
        self._toggle_value("show_all_layers")

    def toggle_hide_specific_layers(self, class_name: str):
        """Toggles temporary invisibility for all active layers of type `className`."""
        if (class_name in self.hide_specific_layers):
            self.hide_specific_layers[class_name] = not self.hide_specific_layers[class_name]
        else:
            self.hide_specific_layers[class_name] = True
        self.update_layers()

    def update_layers(self):
        """Update visuals for everything that needs actual frame/layer visuals."""
        frame, time = self.app.timeline_manager.time_tuple
        self.app.circuit_manager.resolve(frame, time)
        surfaces = self.composite(frame, time)
        self.app.main_window.canvas_pane.present(surfaces)
        self.app.main_window.timeline_widget.onUpdate()

    def update_layer_texts(self):
        """Update visuals for the properties menu and the layer tree widget."""
        self.app.main_window.populate_layers_menu()
        self.app.input_manager.refresh_properties_pane()

    def advance(self, dt: float):
        """Call when playing the animation to update the timeline and the canvas."""
        frame, time = self.app.timeline_manager.advance(dt)
        self.app.circuit_manager.resolve(frame, time)
        surfaces = self.app.layer_manager.composite(frame, time)
        self.app.main_window.canvas_pane.present(surfaces)
