from enum import Enum
from functools import partial

from PySide6.QtCore import QSize, Qt, QSignalBlocker
from PySide6.QtGui import QColor, QIcon, QMouseEvent
from PySide6.QtWidgets import QComboBox, QSizePolicy, QToolButton, QWidget, QCheckBox, QSpinBox, QDoubleSpinBox, QColorDialog, QPushButton, QLabel, QHBoxLayout, QLayout, QLineEdit
from typing import Callable, Any, TYPE_CHECKING, TypeVar
from core.dynamic_value import DynamicValue
from core.paths import resource_path
from core.vectors import Vec2, Vec3, VectorBase
if TYPE_CHECKING:
    from app import App
from shiboken6 import isValid


class Property[T]:
    """A property. Can change based on the frame, or can be bounded, """

    def __init__(self, app: "App", id: str, name: str, default: T, on_modify: Callable[[T], None] | None = None, min_value: Any = None, max_value: Any = None, bounder: Callable[[Any, Any, T], T] | None = None):
        self.id = id
        self.name = name
        self.dynamic_value = DynamicValue(
            app, default, min_value, max_value, bounder, name)
        if on_modify != None:
            self.dynamic_value._on_modify += on_modify

    @property
    def value(self) -> T:
        """Get the current value of the property, at the current frame."""
        return self.dynamic_value.current_value

    @property
    def keyframe_value(self) -> T:
        """If there is a keyframe here, gets its exact value. Else acts exactly like `value`."""
        return self.dynamic_value.keyframe_value

    def resolve(self):
        """Update the current value of the property to that of the current frame."""
        self.dynamic_value.resolve(
            self.dynamic_value.app.timeline_manager.current_frame)

    def get_value_at(self, frame: int, get_keyframe: bool = True) -> T:
        """Get the value of the property at a specified frame. If get_keyframe and there's a keyframe on this frame, gets the exact value of the keyframe instead of its bounded value."""
        return self.dynamic_value.get_value_at(frame, get_keyframe)

    def on_modify(self, on_modify: Callable[[Any], None]):
        """Call the specified function when the property's current value changes. This includes when the frame changes, changing the current value."""
        self.dynamic_value._on_modify += on_modify


class PropertySeparator:
    """A break in a property widget."""

    def __init__(self, id: str):
        self.id = id


class PropertyTitle:
    """A title for a section of a property widget."""

    def __init__(self, id: str, name: str):
        self.id, self.name = id, name


class PropertyButton:
    """A button for a property widget that, when pressed, calls a specified function."""

    def __init__(self, id: str, name: str, click: Callable):
        self.id, self.name, self.click = id, name, click


class PropertiesDict:
    def __init__(self, app: "App") -> None:
        self.app = app
        self.properties = list[Property | PropertySeparator |
                               PropertyTitle | PropertyButton]()

    def items(self) -> list[Property]:
        newList = list[Property]()
        for t in self.properties:
            newList.append(t) if isinstance(t, Property) else ""
        return newList

    def clear(self) -> None:
        self.properties.clear()

    def __getitem__(self, id: str) -> Property:
        return self.get_property(id)

    def __setitem__(self, id: str, value: Property) -> Any:
        for i in range(len(self.properties)):
            if isinstance(v := self.properties[i], Property) and v.id == id:
                self.properties[i] = value
                return

        self.properties.append(value)

    def remove_at(self, index: int):
        self.properties.pop(index)

    TProperty = TypeVar("TProperty", bound=Property |
                        PropertySeparator | PropertyTitle | PropertyButton)

    def _get_object_of_type_(self, t: type[TProperty], id: str) -> TProperty:
        for x in self.properties:
            if isinstance(x, t) and x.id == id:
                return x

        try:
            raise KeyError(f"Key \"{id}\" not in dict")
        except KeyError as e:
            e.with_traceback(None)
            raise

    def get_property(self, id: str) -> Property:
        return self._get_object_of_type_(Property, id)

    def get_separator(self, id: str) -> PropertySeparator:
        return self._get_object_of_type_(PropertySeparator, id)

    def get_title(self, id: str) -> PropertyTitle:
        return self._get_object_of_type_(PropertyTitle, id)

    def get_button(self, id: str) -> PropertyButton:
        return self._get_object_of_type_(PropertyButton, id)

    def __iadd__(self, other: Property | PropertySeparator | PropertyTitle | PropertyButton, index=-1):
        if (index == -1):
            self.properties.append(other)
        else:
            self.properties.insert(index, other)
        return self

    def add_property(self, id: str, name: str, default, on_modify: Callable[[Any], None] | None = None, min_value: Any = None, max_value: Any = None, bounder: Callable[[Any, Any, Any], Any] | None = None, index: int = -1):
        self.__iadd__(Property(self.app, id, name, default, on_modify,
                      min_value, max_value, bounder), index)

    def add_separator(self, id: str, index: int = -1):
        self.__iadd__(PropertySeparator(id), index)

    def add_title(self, id: str, name: str, index: int = -1):
        self.__iadd__(PropertyTitle(id, name), index)

    def add_button(self, id: str, name: str, click: Callable, index: int = -1):
        self.__iadd__(PropertyButton(id, name, click), index)

    def _index_of_type_(self, t: type[Property | PropertySeparator | PropertyTitle | PropertyButton], id: str):
        for i, x in enumerate(self.properties):
            if isinstance(x, t) and x.id == id:
                return i
        return -1

    def index_of_property(self, id: str) -> int:
        return self._index_of_type_(Property, id)

    def index_of_separator(self, id: str) -> int:
        return self._index_of_type_(PropertySeparator, id)

    def index_of_title(self, id: str) -> int:
        return self._index_of_type_(PropertyTitle, id)

    def index_of_button(self, id: str) -> int:
        return self._index_of_type_(PropertyButton, id)


class HasProperties:
    def __init__(self, app: "App") -> None:
        self.properties = PropertiesDict(app)
        self.app = app
        self.is_tool = False
        super().__init__()

    def render_properties_ui(self, pane: QWidget):
        """Populate `pane` (which has a `QVBoxLayout`) with property editors. By default, uses `self.properties`. \n
        `pane` is already clear here."""
        layout = pane.layout()
        if isinstance(layout, QLayout):
            for value in self.properties.properties:
                if (isinstance(value, Property)):
                    value_type = value.dynamic_value.value_type
                    vlue = value.keyframe_value
                    # add_outer_shell: bool = True
                    new_widget: QWidget | None = None
                    value_modify_func: Callable | None = None

                    # My error-checking gets mad without this :(
                    if issubclass(value_type, str) and isinstance(vlue, str):
                        new_widget = QLineEdit()
                        new_widget.setText(vlue)
                        new_widget.setReadOnly(
                            value.dynamic_value.is_circuit_driven)

                        def on_str_value_modify(newValue, v=value, w=new_widget):
                            if not isValid(w):
                                if on_str_value_modify in v.dynamic_value._on_modify:
                                    v.dynamic_value._on_modify -= on_str_value_modify
                            if isinstance(newValue, str) and isValid(w):
                                with QSignalBlocker(w):
                                    cursor_pos = w.cursorPosition()
                                    w.setText(newValue)
                                    w.setCursorPosition(cursor_pos)
                        value_modify_func = on_str_value_modify

                        def on_str_input_modify(s: str, v=value, w=new_widget):
                            v.dynamic_value.current_value = s
                            self.app.layer_manager.update_layers()
                        new_widget.textChanged.connect(on_str_input_modify)

                    elif issubclass(value_type, bool) and isinstance(vlue, bool):
                        new_widget = QCheckBox()
                        new_widget.setChecked(vlue)
                        new_widget.setCheckable(
                            not value.dynamic_value.is_circuit_driven)

                        def on_bool_value_modify(newValue, v=value, w=new_widget):
                            if not isValid(w):
                                if on_bool_value_modify in v.dynamic_value._on_modify:
                                    v.dynamic_value._on_modify -= on_bool_value_modify
                            if isinstance(newValue, bool) and isValid(w):
                                with QSignalBlocker(w):
                                    w.setChecked(newValue)
                        value_modify_func = on_bool_value_modify

                        def on_bool_input_modify(state: Qt.CheckState, v=value, w=new_widget):
                            v.dynamic_value.current_value = state == Qt.CheckState.Checked
                            self.app.layer_manager.update_layers()
                        new_widget.checkStateChanged.connect(
                            on_bool_input_modify)

                    elif issubclass(value_type, int) and isinstance(vlue, int):
                        new_widget = QSpinBox()
                        new_widget.setMinimum(-2147483648)
                        new_widget.setMaximum(2147483647)
                        new_widget.setValue(vlue)
                        new_widget.setReadOnly(
                            value.dynamic_value.is_circuit_driven)

                        def on_int_value_modify(newValue, v=value, w=new_widget):
                            if not isValid(w):
                                if on_int_value_modify in v.dynamic_value._on_modify:
                                    v.dynamic_value._on_modify -= on_int_value_modify
                            if isinstance(newValue, int) and isValid(w):
                                with QSignalBlocker(w):
                                    w.setValue(newValue)
                        value_modify_func = on_int_value_modify

                        def on_int_input_modify(i: int, v=value, w=new_widget):
                            v.dynamic_value.current_value = i
                            self.app.layer_manager.update_layers()
                        new_widget.valueChanged.connect(on_int_input_modify)

                    elif issubclass(value_type, float) and isinstance(vlue, float):
                        new_widget = QDoubleSpinBox()
                        new_widget.setMinimum(-float('inf'))
                        new_widget.setMaximum(float('inf'))
                        new_widget.setDecimals(8)
                        new_widget.setValue(vlue)
                        new_widget.setReadOnly(
                            value.dynamic_value.is_circuit_driven)

                        def on_float_value_modify(newValue, v=value, w=new_widget):
                            if not isValid(w):
                                if on_float_value_modify in v.dynamic_value._on_modify:
                                    v.dynamic_value._on_modify -= on_float_value_modify
                            if isinstance(newValue, float) and isValid(w):
                                with QSignalBlocker(w):
                                    w.setValue(newValue)
                        value_modify_func = on_float_value_modify

                        def on_float_input_modify(d: float, v=value, w=new_widget):
                            v.dynamic_value.current_value = d
                            self.app.layer_manager.update_layers()
                        new_widget.valueChanged.connect(on_float_input_modify)

                    elif issubclass(value_type, QColor) and isinstance(vlue, QColor):
                        new_widget = QPushButton()
                        new_widget.setStyleSheet(
                            f"background-color: {vlue.name()};")
                        new_widget.setEnabled(
                            not value.dynamic_value.is_circuit_driven)

                        def on_qcolor_value_modify(newValue, v=value, w=new_widget):
                            if not isValid(w):
                                if on_qcolor_value_modify in v.dynamic_value._on_modify:
                                    v.dynamic_value._on_modify -= on_qcolor_value_modify
                            if isinstance(newValue, QColor) and isValid(w):
                                with QSignalBlocker(w):
                                    w.setStyleSheet(
                                        f"background-color: {newValue.name()};")

                        value_modify_func = on_qcolor_value_modify

                        def on_qcolor_input_modify(checked=False, w=new_widget, v=value):
                            color = QColorDialog.getColor(
                                v.value, pane, v.name)
                            if color.isValid():
                                v.dynamic_value.current_value = color
                                w.setStyleSheet(
                                    f"background-color: {color.name()};")
                                self.app.layer_manager.update_layers()
                        new_widget.clicked.connect(on_qcolor_input_modify)

                    elif issubclass(value_type, (Vec2, Vec3)) and isinstance(vlue, (Vec2, Vec3)):
                        new_widget, value_modify_func = self.create_vector_widget(
                            value)

                    elif issubclass(value_type, Enum) and isinstance(vlue, Enum):
                        new_widget = QComboBox()
                        for i, e in enumerate(value_type):
                            new_widget.addItem(e.name, e)
                            if (e == vlue):
                                new_widget.setCurrentIndex(i)

                        def on_enum_value_modify(newValue, v=value, w=new_widget, t=value_type):
                            if not isValid(w):
                                if on_enum_value_modify in v.dynamic_value._on_modify:
                                    v.dynamic_value._on_modify -= on_enum_value_modify
                            if isinstance(newValue, t) and isValid(w):
                                with QSignalBlocker(w):
                                    w.setCurrentIndex(
                                        [e for e in t].index(newValue))

                        value_modify_func = on_enum_value_modify

                        def on_enum_input_modify(i: int, w=new_widget, v=value, t=value_type):
                            if (i != -1):
                                v.dynamic_value.current_value = [
                                    e for e in t][i]
                            else:
                                on_enum_value_modify(w.currentIndex())
                        new_widget.currentIndexChanged.connect(
                            on_enum_input_modify)

                    if value_modify_func != None:
                        value.dynamic_value._on_keyframe_modify += value_modify_func

                    def on_widget_delete(*, v=value):
                        if value_modify_func in v.dynamic_value._on_keyframe_modify and value_modify_func != None:
                            v.dynamic_value._on_keyframe_modify -= value_modify_func
                    new_widget.destroyed.connect(
                        on_widget_delete) if new_widget != None else ""

                    if new_widget != None:  # `add_outer_shell and `
                        row_layout = QHBoxLayout(row := QWidget())
                        row_layout.setContentsMargins(0, 0, 0, 0)

                        row_layout.addWidget(QLabel(value.name))
                        if not self.is_tool:
                            button = PropertyDiamondButton(
                                self.app, value, pane, toolButtonStyle=Qt.ToolButtonStyle.ToolButtonIconOnly)
                            row_layout.addWidget(button)

                        row_layout.addWidget(new_widget)

                        layout.addWidget(row)
                    elif new_widget != None:
                        layout.addWidget(new_widget)
                elif isinstance(value, PropertySeparator):
                    layout.addWidget(QWidget(minimumHeight=15))
                elif isinstance(value, PropertyTitle):
                    layout.addWidget(QWidget(minimumHeight=10))
                    layout.addWidget(label := QLabel(value.name))
                    font = label.font()
                    font.setPointSize(int(font.pointSize() * 1.5))
                    font.setBold(True)
                    label.setFont(font)
                elif isinstance(value, PropertyButton):
                    layout.addWidget(widget := QPushButton())
                    widget.setText(value.name)
                    widget.clicked.connect(value.click)

    def create_vector_widget(self, value: Property[VectorBase]) -> tuple[QWidget, Callable]:
        vlue = value.keyframe_value
        vec_type = type(vlue)
        axes = vec_type.axisMapping
        # Returns (widget, cleanup_callback)

        new_widget = QWidget()
        widget_layout = QHBoxLayout(new_widget)

        widgets: list[QDoubleSpinBox] = []

        def on_vec3_value_modify(newValue, w: list[QDoubleSpinBox] = widgets, a: list[str] = axes, t=vec_type):
            if not isValid(w):
                if on_vec3_value_modify in value.dynamic_value._on_modify:
                    value.dynamic_value._on_modify -= on_vec3_value_modify
            isFullyValid = True
            for widget in w:
                if not isValid(widget):
                    isFullyValid = False

            if isinstance(newValue, t) and isFullyValid:
                for widget, axis in zip(w, a):
                    with QSignalBlocker(widget):
                        widget.setValue(newValue[axis])

        for axis in axes:
            widget_layout.addWidget(QLabel(axis + ":"))
            widget_layout.addWidget(widget := QDoubleSpinBox())
            widget.setMinimum(-float('inf'))
            widget.setMaximum(float('inf'))
            widget.setDecimals(8)
            widget.setValue(vlue[axis])
            widget.setReadOnly(value.dynamic_value.is_circuit_driven)

            def on_vec3_input_modify(d: float, v=value, i=axis, t=vec_type):
                if isinstance(v.dynamic_value.current_value, t):
                    vec = v.dynamic_value.current_value.clone()
                    vec[i] = d
                    v.dynamic_value.current_value = vec
                    self.app.layer_manager.update_layers()
            widget.valueChanged.connect(on_vec3_input_modify)
            widgets.append(widget)

        return new_widget, on_vec3_value_modify


class PropertyDiamondButton(QToolButton):
    def __init__(self, app: "App", property: Property, *args, **kwargs):
        self.app = app
        self.prop = property
        super().__init__(*args, **kwargs)
        self.set_styles()
        self.app.timeline_manager.on_time_change += self.set_icon
        self.prop.on_modify(self.set_icon)

    def set_styles(self):
        self.set_icon()
        self.setIconSize(QSize(20, 20))
        self.setContentsMargins(0, 0, 0, 0)
        self.setStyleSheet(
            "QToolButton { padding: 0px; margin: 0px; background-color: transparent; border: 0px; }")
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.setFixedWidth(25)
        self.setFixedHeight(25)

    def mousePressEvent(self, event: QMouseEvent):
        if Qt.KeyboardModifier.ControlModifier in event.modifiers():
            self.prop.dynamic_value.delete_keyframe_at(
                self.app.timeline_manager.current_frame)
            self.app.layer_manager.update_layers()
        elif event.button() == Qt.MouseButton.LeftButton:
            self.app.main_window.switch_to_keyframe_widget(self.prop)
        elif event.button() == Qt.MouseButton.RightButton:
            self.prop.dynamic_value.create_keyframe_at(
                self.app.timeline_manager.current_frame, self.prop.dynamic_value.get_value_at(self.app.timeline_manager.current_frame, False))
        self.set_icon()
        super().mousePressEvent(event)

    def set_icon(self, *_):
        if not isValid(self):
            self._cleanup()
            return

        url = ("blue_timeline_diamond.png" if not self.prop.dynamic_value.has_keyframe_at(self.app.timeline_manager.current_frame)
               else "key_timeline_diamond") if self.prop.dynamic_value._is_keyframed else "grey_timeline_diamond.png"
        self.setIcon(
            QIcon(resource_path("images", url).as_posix()))

    def _cleanup(self):
        self.app.timeline_manager.on_time_change -= self.set_icon
        self.prop.dynamic_value._on_modify -= self.set_icon
