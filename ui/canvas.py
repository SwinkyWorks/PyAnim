# QOpenGLWidget - the viewport
from PySide6.QtCore import QRect, Qt, QSize, QPoint, QTimer, QElapsedTimer
from PySide6.QtGui import QPainter, QColor, QImage, QMouseEvent, QWheelEvent, QPaintEvent
from PySide6.QtWidgets import QWidget
from typing import TYPE_CHECKING
from core.vectors import Vec2
if TYPE_CHECKING:
    from app import App
import sys


class Canvas(QWidget):
    def __init__(self, app: "App", parent: QWidget | None = None):
        super().__init__(parent)
        self.app = app
        self.drag_pos = Vec2()
        self.scroll_level = 1
        self.drawWindow = QImage(
            self.app.layer_manager.size, QImage.Format.Format_ARGB32)
        self.drawWindow.fill(Qt.GlobalColor.transparent)
        self.isMouseDown = False
        self.prevMousePos = Vec2()
        self.elapsed = QElapsedTimer()
        self.elapsed.start()
        self.last_frame_time_stamp = self.elapsed.nsecsElapsed() / 1000000
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.tick)
        self.timer.start(0)
        self.setMouseTracking(True)

    def paintEvent(self, event: QPaintEvent):
        painter = QPainter(self)
        try:
            painter.fillRect(self.rect(), QColor(100, 100, 100))

            if (self.drag_pos.x < -self.app.layer_manager.size.width() / 2.0):
                self.drag_pos.x = -self.app.layer_manager.size.width() / 2.0
            if (self.drag_pos.x > self.app.layer_manager.size.width() / 2.0):
                self.drag_pos.x = self.app.layer_manager.size.width() / 2.0
            if (self.drag_pos.y < -self.app.layer_manager.size.height() / 2.0):
                self.drag_pos.y = -self.app.layer_manager.size.height() / 2.0
            if (self.drag_pos.y > self.app.layer_manager.size.height() / 2.0):
                self.drag_pos.y = self.app.layer_manager.size.height() / 2.0

            if (self.scroll_level < 0.00001):
                self.scroll_level = 0.00001
            if (self.scroll_level > 100000):
                self.scroll_level = 100000

            # division not directly supported for some reason
            size: QSize = self.app.layer_manager.size * (1 / self.scroll_level)

            thisPos = self.posToPixel(Vec2(0, 0))

            newRect = QRect(int(thisPos.x), int(thisPos.y),
                            size.width(), size.height())

            painter.fillRect(newRect, Qt.GlobalColor.white)

            painter.drawImage(newRect, self.drawWindow)

            self.app.input_manager.on_canvas_method("paint", painter=painter)
        finally:
            painter.end()

    def present(self, surfaces: list[QImage]):
        if (self.drawWindow.size() != self.app.layer_manager.size):
            self.drawWindow = QImage(
                self.app.layer_manager.size, QImage.Format.Format_ARGB32)
        self.drawWindow.fill(Qt.GlobalColor.transparent)
        painter = QPainter(self.drawWindow)
        try:
            for surface in surfaces:
                painter.drawImage(QPoint(0, 0), surface)
        finally:
            painter.end()
        self.update()  # trigger paintEvent

    def resize(self, *args) -> None:
        super().resize(*args)
        self.update()  # trigger paintEvent

    def mousePressEvent(self, event: QMouseEvent) -> None:
        super().mousePressEvent(event)
        modified_pos = self.pixelToPos(Vec2(event.pos()))
        self.prevMousePos = modified_pos
        self.app.input_manager.on_canvas_method(
            "press", x=modified_pos.x, y=modified_pos.y)
        self.isMouseDown = True

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        super().mouseMoveEvent(event)
        pos = self.pixelToPos(Vec2(event.pos()))

        if (self.isMouseDown):
            self.app.input_manager.on_canvas_method("drag",
                                                    x=pos.x, y=pos.y, dx=pos.x - self.prevMousePos.x, dy=pos.y - self.prevMousePos.y)
        else:
            self.app.input_manager.on_canvas_method("move",
                                                    x=pos.x, y=pos.y, dx=pos.x - self.prevMousePos.x, dy=pos.y - self.prevMousePos.y)

        self.prevMousePos = pos

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        super().mouseReleaseEvent(event)
        modified_pos = self.pixelToPos(Vec2(event.pos()))
        self.prevMousePos = modified_pos
        self.app.input_manager.on_canvas_method("release",
                                                x=modified_pos.x, y=modified_pos.y)
        self.isMouseDown = False

    def pixelToPos(self, event_pos: Vec2):
        # hoo boy am I glad I added those conversions
        # this makes this calculation a whole lot easier
        return (Vec2(event_pos) - Vec2(self.size()) / 2) * \
            self.scroll_level - self.drag_pos + \
            Vec2(self.app.layer_manager.size) / 2

    def posToPixel(self, pos: Vec2) -> Vec2:
        # dragPos is middle pos minus half screen size, so at (0,0) it would be centered at any scroll_level
        return (pos + self.drag_pos - Vec2(self.app.layer_manager.size) / 2) / self.scroll_level + Vec2(self.size()) / 2

    # scrollEvent but temu
    def wheelEvent(self, event: QWheelEvent) -> None:
        mousePos = Vec2(event.position().toPoint()) - Vec2(self.size()) / 2
        self.drag_pos -= mousePos * self.scroll_level

        numPixels = event.pixelDelta().y()
        numPixels = event.angleDelta().y() / 8.0 if numPixels == 0 else numPixels
        self.scroll_level *= pow(0.999, float(numPixels))

        self.drag_pos += mousePos * self.scroll_level
        self.update()

    def tick(self):
        time_stamp = self.elapsed.nsecsElapsed() / 1000000
        dt = (time_stamp - self.last_frame_time_stamp) / 1000
        self.last_frame_time_stamp = time_stamp
        self.app.input_manager.on_canvas_method("frame", deltaTime=dt)

    def reset_scroll(self):
        self.scroll_level, self.drag_pos = 1.0, Vec2(
            0, 0)


# pixel
# prev - self.size() / 2
# prev * self.scroll_level
# prev - self.drag_pos
# prev + self.app.layer_manager.size / 2

# pixel
# pixel - self.size() / 2
# (pixel - self.size() / 2) * self.scroll_level
# (pixel - self.size() / 2) * self.scroll_level - self.drag_pos
# (pixel - self.size() / 2) * self.scroll_level - self.drag_pos + self.app.layer_manager.size / 2
# (pixel - self.size() / 2) * self.scroll_level - self.drag_pos + self.app.layer_manager.size / 2 = pos

# (  a   -      b      / 2) *         c         -      d        +             e               / 2 =  f
# (a - b / 2) * c - d + e / 2   =   f
# (a - b / 2) * c   =   f + d - e / 2
# a - b / 2   =   (f + d - e / 2) / c
# a   =   (f + d - e / 2) / c + b / 2

# pixel = (pos + self.drag_pos - self.app.layer_manager.size / 2) / self.scroll_level + self.size() / 2
