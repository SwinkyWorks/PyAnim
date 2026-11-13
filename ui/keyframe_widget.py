from PySide6.QtCore import Qt
from PySide6.QtGui import QImage, QMouseEvent, QPaintEvent, QPainter, QPen, QColor
from PySide6.QtWidgets import QComboBox, QDoubleSpinBox, QHBoxLayout, QLabel, QScrollArea, QSplitter, QVBoxLayout, QWidget
from core.dynamic_value import DynamicValue
from core.interpolation_modes import BaseInterpolation
from core.paths import resource_path
from numbers import Real
from shiboken6 import isValid
from core.pyside6_helpers import clear_layout
from core.vectors import Vec2

from typing import TYPE_CHECKING, Any, cast
if TYPE_CHECKING:
    from app import App


class KeyframeWidget(QSplitter):
    def __init__(self, app: "App", parent: QWidget):
        super().__init__(Qt.Orientation.Horizontal, parent)
        self.app = app
        self._selected_keyframe: tuple[KeyframeGraph, int] | None = None

        self.graph_splitter = QSplitter(Qt.Orientation.Horizontal)

        # Property headers
        self.headers_scroll = QScrollArea()
        self.headers_scroll.setWidgetResizable(True)
        self.headers_scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self.headers_scroll.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self.headers_widget = QWidget()
        self.headers_layout = QVBoxLayout(self.headers_widget)
        self.headers_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.headers_scroll.setWidget(self.headers_widget)
        self.headers_scroll.setMinimumWidth(200)
        self.headers_layout.setSpacing(0)
        self.headers_layout.setContentsMargins(0, 0, 0, 0)

        # Graph area
        self.graphs_scroll = QScrollArea()
        self.graphs_scroll.setWidgetResizable(True)
        self.graphs_scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self.graphs_scroll.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOn)

        self.graphs_widget = QWidget()
        self.graphs_layout = QVBoxLayout(self.graphs_widget)
        self.graphs_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.graphs_scroll.setWidget(self.graphs_widget)
        self.graphs_scroll.setMinimumWidth(200)
        self.graphs_layout.setSpacing(0)
        self.graphs_layout.setContentsMargins(0, 0, 0, 0)

        self.graph_splitter.addWidget(self.headers_scroll)
        self.graph_splitter.addWidget(self.graphs_scroll)

        self.headers_scroll.verticalScrollBar().valueChanged.connect(
            self.graphs_scroll.verticalScrollBar().setValue
        )
        self.graphs_scroll.verticalScrollBar().valueChanged.connect(
            self.headers_scroll.verticalScrollBar().setValue
        )

        # Right-side inspector panel
        self.inspector_panel = QWidget()
        self.inspector_layout = QVBoxLayout(self.inspector_panel)
        self.inspector_panel.setMinimumWidth(200)
        self.inspector_panel.setMinimumHeight(100)
        self.inspector_panel.setVisible(False)  # Hidden by default

        # Title showing what's selected
        self.inspector_title = QLabel("No keyframe selected")
        self.inspector_title.setStyleSheet(
            "font-weight: bold; font-size: 14px;")
        self.inspector_layout.addWidget(self.inspector_title)

        # Property editors will go here
        self.inspector_scroll = QScrollArea()
        self.inspector_content = QWidget()
        self.inspector_content.setMinimumHeight(100)
        self.inspector_content_layout = QVBoxLayout(self.inspector_content)
        self.inspector_content_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.inspector_scroll.setWidget(self.inspector_content)
        self.inspector_scroll.setWidgetResizable(True)
        self.inspector_layout.addWidget(self.inspector_scroll)

        # Add both to main splitter
        self.addWidget(self.graph_splitter)
        self.addWidget(self.inspector_panel)

        # Start with inspector collapsed
        self.setSizes([1000, 0])

        self.updateRows()

    @property
    def selected_keyframe(self):
        return self._selected_keyframe

    @selected_keyframe.setter
    def selected_keyframe(self, value: tuple["KeyframeGraph", int] | None):
        old = self._selected_keyframe
        self._selected_keyframe = value
        if old != None and isValid(old[0]):
            old[0].update()
        if value != None:
            value[0].update()
            self.show_keyframe_inspector(
                value[0].value._keyframes[value[1]], value[1], value[0])
        else:
            self.hide_keyframe_inspector()

    def updateRows(self):
        clear_layout(self.headers_layout)
        clear_layout(self.graphs_layout)
        for value in self.app.timeline_manager.keyframed_values:
            new_header = QLabel()
            new_header.setFixedHeight(100)
            new_header.setText(value.name)
            font = new_header.font()
            font.setPointSize(int(font.pointSize() * 2))
            font.setBold(True)
            new_header.setFont(font)
            new_header.setAlignment(Qt.AlignmentFlag.AlignTop)
            new_header.setStyleSheet("border: 2px solid #333;")
            self.headers_layout.addWidget(new_header)

            new_graph = KeyframeGraph(self.app, value)
            new_graph.setFixedHeight(100)
            new_graph.setStyleSheet("border: 2px solid #333;")
            self.graphs_layout.addWidget(new_graph)

    def show_keyframe_inspector(self, keyframe_tuple: tuple[int, Any, BaseInterpolation], index: int, graph: "KeyframeGraph"):
        self.inspector_panel.setVisible(True)
        self.setSizes([700, 300])  # Expand inspector
        self.inspector_title.setText(
            f"Keyframe at frame {keyframe_tuple[0]}")

        clear_layout(self.inspector_content_layout)

        interpolation = keyframe_tuple[2]

        mode = QComboBox()
        for i, t in enumerate([
            k
            for k in self.app.timeline_manager.registered_interpolation_modes.values()
            if any(
                [
                    issubclass(graph.value.value_type, a)
                    for a in k[1].available_types
                ]
            )
        ]):
            mode.addItem(t[1].name, t)
            if (isinstance(interpolation, t[1])):
                mode.setCurrentIndex(i)

        def update_inspector_properties():
            if self._selected_keyframe == None:
                return
            kf = self._selected_keyframe[0].value._keyframes[self._selected_keyframe[1]]
            for i in reversed(range(1, self.inspector_content_layout.count())):
                item = self.inspector_content_layout.itemAt(i)
                if item != None:
                    if (childWidget := item.widget()) != None:
                        childWidget.deleteLater()
                    self.inspector_content_layout.removeItem(item)
            for k, (s, v) in kf[2].properties.items():
                row_layout = QHBoxLayout(row := QWidget())
                row_layout.setContentsMargins(0, 0, 0, 0)

                row_layout.addWidget(QLabel(s))

                widg = QDoubleSpinBox()
                widg.setMinimum(-float("Infinity"))
                widg.setMaximum(float("Infinity"))
                widg.setValue(v)

                def on_widg_modify(d: float, index=k):
                    if (self._selected_keyframe != None):
                        pr = self._selected_keyframe[0].value._keyframes[self._selected_keyframe[1]][2].properties
                        pr[index] = (pr[index][0], d)
                        self._selected_keyframe[0].update()
                widg.valueChanged.connect(on_widg_modify)
                row_layout.addWidget(widg)

                self.inspector_content_layout.addWidget(row)

        def onInterpolationModeChanged(i: int, m=mode, g=graph):
            t: type[BaseInterpolation] = m.currentData()[1]
            interpolation = t()
            k = g.value._keyframes
            k[index] = k[index][0], k[index][1], interpolation
            update_inspector_properties()

        mode.currentIndexChanged.connect(onInterpolationModeChanged)
        self.inspector_content_layout.addWidget(mode)
        update_inspector_properties()

    def hide_keyframe_inspector(self):
        self.inspector_panel.setVisible(False)
        self.setSizes([1000, 0])  # Collapse inspector

        self.inspector_title.setText("No keyframe selected")
        clear_layout(self.inspector_content_layout)


class KeyframeGraph(QWidget):
    def __init__(self, app: "App", value: DynamicValue) -> None:
        super().__init__()
        self.app = app
        self.value = value
        self.value._on_modify += self.update_graph
        self.update_scale(1000.0)
        self.app.timeline_manager.on_new_frame += self.update_graph
        self.app.timeline_manager.on_duplicated_frame += self.update_graph
        self.app.timeline_manager.on_deleted_frame += self.update_graph
        self.app.timeline_manager.on_moved_frame += self.update_graph
        self.app.timeline_manager.on_time_change += self.update_graph
        self.dragged_keyframe: int = -1
        self.drag_pos: Vec2 | None = None
        self.dragging: bool = False

    def paintEvent(self, event: QPaintEvent) -> None:
        if self.check_for_deletion():
            return
        painter = QPainter(self)

        try:
            self.draw_background(painter)
            kfs = KeyframeGraph.get_kfs(self.value._keyframes)

            pen = QPen(QColor("#44f"), 4)
            painter.setPen(pen)

            scale = KeyframeGraph.get_scale(kfs, self.height())

            self.draw_graph(painter, kfs, scale)

            self.draw_keyframes(painter, kfs, scale)
        finally:
            painter.end()

    def draw_background(self, painter: QPainter):
        painter.fillRect(self.rect(), Qt.GlobalColor.black)

        pen = QPen(QColor("#333"), 4)
        painter.setPen(pen)
        painter.drawRect(self.rect())
        for i in range(self.app.timeline_manager.num_frames):
            x = int((self.app.timeline_manager.time_at_frame(
                i) + self.app.timeline_manager.frames[i].frametime / 2) * self.scale)
            painter.drawLine(x, 0, x, self.height())

        pen.setColor("#666")
        painter.setPen(pen)

        x = int((self.app.timeline_manager.current_time +
                self.app.timeline_manager.frames[self.app.timeline_manager.current_frame].frametime / 2) * self.scale)
        painter.drawLine(x, 0, x, self.height())

    @staticmethod
    def get_sorted_kfs(keyframes: list[tuple[int, Any, BaseInterpolation]]):
        return sorted(KeyframeGraph.get_kfs(keyframes), key=lambda a: a[0])

    @staticmethod
    def get_kfs(keyframes: list[tuple[int, Any, BaseInterpolation]]):
        return [(a[0], (float(a[1]) if isinstance(a[1], Real) else 0.0), a[2]) for a in keyframes]

    @staticmethod
    def get_scale(keyframes: list[tuple[int, float, BaseInterpolation]], height: int):
        minV = min([cast(float, a[1])
                   for a in keyframes]) if len(keyframes) > 0 else 0.0
        maxV = max([cast(float, a[1])
                   for a in keyframes]) if len(keyframes) > 0 else 0.0
        eq = minV == maxV
        vScale = (1.0 / (maxV - minV) *
                  (height * 3/4)) if not eq else 0.0
        return (minV, maxV, eq, vScale)

    def draw_graph(self, painter: QPainter, keyframes: list[tuple[int, float, BaseInterpolation]], scale: tuple[float, float, bool, float]):
        minV, maxV, eq, vScale = scale
        kfs = sorted(keyframes, key=lambda a: a[0])
        if len(kfs) > 1 and not eq:
            start_frame, end_frame = min(max(0, int(kfs[0][0])), self.app.timeline_manager.num_frames - 1), min(
                max(0, int(kfs[-1][0])), self.app.timeline_manager.num_frames - 1)

            painter.drawLine(
                0,
                (int((-kfs[0][1] + maxV) * vScale +
                 (self.height() / 8)) if not eq else self.height() // 2),
                int((self.app.timeline_manager.time_at_frame(start_frame) +
                    self.app.timeline_manager.frames[start_frame].frametime / 2) * self.scale),
                (int((-kfs[0][1] + maxV) * vScale +
                 (self.height() / 8)) if not eq else self.height() // 2)
            )
            rate = 40
            f = start_frame
            d = 0
            while f < end_frame:
                if f < 0 or f >= self.app.timeline_manager.num_frames:
                    continue
                at = (self.app.timeline_manager.time_at_frame(f) +
                      self.app.timeline_manager.frames[f].frametime * d / rate)
                ax = (
                    at + self.app.timeline_manager.frames[f].frametime / 2) * self.scale
                av = self.value.get_value_at_time(at, False)
                ay = float(av) if isinstance(av, Real) else 0.0
                f += (1 if d >= rate else 0)
                d += (1 if d < rate else -d)
                if f < 0 or f >= self.app.timeline_manager.num_frames:
                    continue
                bt = (self.app.timeline_manager.time_at_frame(f) +
                      self.app.timeline_manager.frames[f].frametime * d / rate)
                bx = (
                    bt + self.app.timeline_manager.frames[f].frametime / 2) * self.scale
                bv = self.value.get_value_at_time(bt, False)
                by = float(bv) if isinstance(bv, Real) else 0.0
                painter.drawLine(int(ax), int((-ay + maxV) * vScale + (self.height() / 8)),
                                 int(bx), int((-by + maxV) * vScale + (self.height() / 8)))

            painter.drawLine(
                int((self.app.timeline_manager.time_at_frame(
                    end_frame) + self.app.timeline_manager.frames[end_frame].frametime / 2) * self.scale),
                (int((-kfs[-1][1] + maxV) * vScale +
                 (self.height() / 8)) if not eq else self.height() // 2),
                int(self.app.timeline_manager.max_time * self.scale),
                (int((-kfs[-1][1] + maxV) * vScale +
                 (self.height() / 8)) if not eq else self.height() // 2)
            )
        else:
            painter.drawLine(0, self.height() // 2, int(
                self.app.timeline_manager.max_time * self.scale), self.height() // 2)

    def draw_keyframes(self, painter: QPainter, keyframes: list[tuple[int, float, BaseInterpolation]], scale: tuple[float, float, bool, float]):
        minV, maxV, eq, vScale = scale
        image = QImage(resource_path(
            "images", "key_timeline_diamond.png").as_posix())
        for i, (frame, value, _) in enumerate(keyframes):
            if frame < 0 or frame > self.app.timeline_manager.num_frames - 1:
                continue
            x = (self.app.timeline_manager.time_at_frame(
                frame) + self.app.timeline_manager.frames[int(frame)].frametime / 2) * self.scale - image.width() / 2
            y = ((-value + maxV) * vScale + (self.height() / 8) -
                 image.height() / 2) if not eq else (self.height() - image.height()) / 2
            if (i == self.dragged_keyframe and self.dragging):
                x, y = self.drag_pos if self.drag_pos != None else (0.0, 0.0)
            if (self.app.main_window.keyframe_widget.selected_keyframe != None and self.app.main_window.keyframe_widget.selected_keyframe[0].value == self.value and self.app.main_window.keyframe_widget.selected_keyframe[1] == i):
                painter.drawImage(int(x) - 1, int(y), image)
                painter.drawImage(int(x), int(y) - 1, image)
                painter.drawImage(int(x) + 1, int(y), image)
                painter.drawImage(int(x), int(y) + 1, image)
            painter.drawImage(int(x), int(y), image)

    def update_scale(self, scale: float):
        self.scale = scale
        self.update_graph()

    def update_graph(self, *_):
        if self.check_for_deletion():
            return
        self.setMinimumWidth(
            int(self.scale * self.app.timeline_manager.max_time))
        self.update()

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if self.check_for_deletion():
            return

        pos = Vec2(event.x(), event.y())
        kfs = KeyframeGraph.get_kfs(self.value._keyframes)
        minV, maxV, eq, vScale = KeyframeGraph.get_scale(kfs, self.height())
        image = QImage(resource_path(
            "images", "key_timeline_diamond.png").as_posix())

        k: tuple[DynamicValue, int] | None = None
        for i, (frame, value, _) in enumerate(kfs):
            x = (self.app.timeline_manager.time_at_frame(
                frame) + self.app.timeline_manager.frames[int(frame)].frametime / 2) * self.scale
            y = ((-value + maxV) * vScale + (self.height() / 8)
                 ) if not eq else self.height() / 2
            fpos = Vec2(x, y)
            if fpos.distance_to(pos) < min(image.width(), image.height()):
                self.app.main_window.keyframe_widget.selected_keyframe = self, i
                self.drag_pos = fpos
                self.dragged_keyframe = i
                super().mousePressEvent(event)
                return

        self.app.main_window.keyframe_widget.selected_keyframe = None
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        pos = Vec2(event.x(), event.y())
        if self.dragging or pos.distance_to(self.drag_pos) > 20:
            self.dragging = True
            self.drag_pos = pos
            self.update()

        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        pos = Vec2(event.x(), event.y())
        if self.dragging or pos.distance_to(self.drag_pos) > 20:
            self.drag_pos = pos
            minV, maxV, eq, vScale = KeyframeGraph.get_scale(
                KeyframeGraph.get_kfs(self.value._keyframes), self.height())

            f = self.app.timeline_manager.frame_at_time(pos.x / self.scale)
            v = self.value._keyframes[self.dragged_keyframe][1]
            if issubclass(self.value.value_type, float) and not eq:
                v = -(pos.y - (self.height() / 8)) / vScale + maxV
            self.value._keyframes[self.dragged_keyframe] = (
                f, v, self.value._keyframes[self.dragged_keyframe][2])

        self.dragging = False
        self.drag_pos = None
        self.dragged_keyframe = -1
        self.update()
        self.app.layer_manager.update_layers()
        self.app.layer_manager.update_layer_texts()

        super().mouseReleaseEvent(event)

    def check_for_deletion(self):
        if (not isValid(self)):
            while self.update_graph in self.app.timeline_manager.on_new_frame:
                self.app.timeline_manager.on_new_frame -= self.update_graph
            while self.update_graph in self.app.timeline_manager.on_duplicated_frame:
                self.app.timeline_manager.on_duplicated_frame -= self.update_graph
            while self.update_graph in self.app.timeline_manager.on_deleted_frame:
                self.app.timeline_manager.on_deleted_frame -= self.update_graph
            while self.update_graph in self.app.timeline_manager.on_moved_frame:
                self.app.timeline_manager.on_moved_frame -= self.update_graph
            while self.update_graph in self.app.timeline_manager.on_time_change:
                self.app.timeline_manager.on_time_change -= self.update_graph
            return True
        return False
