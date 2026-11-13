from PySide6.QtCore import Qt, QSize
from PySide6.QtWidgets import QWidget, QHBoxLayout
from PySide6.QtGui import QImage, QMouseEvent, QPaintEvent, QPen, QScrollEvent, QResizeEvent, QPainter
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from app import App


class TimelineWidget(QWidget):
    def __init__(self, app: "App", /, parent: QWidget | None = None) -> None:
        self.app = app
        super().__init__(parent)
        layout = QHBoxLayout(self)
        self.setLayout(layout)
        layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.images: list[QImage] = []
        self.childWidgets: list[FrameWidget] = []
        self.onUpdate()

    def resizeEvent(self, event: QResizeEvent | None = None):
        self.update()

    def paintEvent(self, event: QPaintEvent) -> None:
        layout = self.layout()
        if layout != None:
            while len(self.childWidgets) < len(self.images):
                widget = FrameWidget(self.app, self)
                widget.index = len(self.childWidgets)
                layout.addWidget(widget)
                self.childWidgets.append(widget)

            while len(self.childWidgets) > len(self.images):
                widget = self.childWidgets.pop()
                layout.removeWidget(widget)
                widget.deleteLater()

            for i in range(len(self.images)):
                widget = self.childWidgets[i]
                image = QImage(self.images[i])

                newWidth = widget.height() * (image.width() / image.height())

                widget.setFixedWidth(int(newWidth))

                widget.setImage(image)

    def scrollEvent(self, event: QScrollEvent):
        self.update()

    def onUpdate(self):
        default_frametime = self.app.timeline_manager.default_frametime
        frame_size: QSize = self.app.layer_manager.size
        current_time = 0.0
        self.images.clear()

        for i, frame in enumerate(self.app.timeline_manager.frames):
            new_image = QImage(frame_size, QImage.Format.Format_ARGB32)
            new_image.fill(Qt.GlobalColor.white)

            layers: list[QImage] = self.app.layer_manager.composite(
                i, current_time)

            painter = QPainter(new_image)
            try:
                j = 0
                for layer in layers:
                    painter.drawImage(new_image.rect(), layer)
                    j += 1
            finally:
                painter.end()

            current_time += frame.frametime if not frame.is_default else default_frametime
            self.images.append(new_image)
        self.update()


class FrameWidget(QWidget):
    def __init__(self, app: "App", parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.app = app
        self.image: QImage | None = None
        self.index: int = 0

    def setImage(self, img: QImage | None):
        self.image = img
        self.update()

    def paintEvent(self, event: QPaintEvent) -> None:
        painter = QPainter(self)
        try:
            painter.fillRect(self.rect(), Qt.GlobalColor.white)
            if self.image is None or self.image.isNull():
                return
            painter.drawImage(self.rect(), self.image)
            if (self.index == self.app.timeline_manager.current_frame):
                p = QPen(Qt.GlobalColor.blue)
                p.setWidth(int(10))
                painter.setPen(p)

                painter.drawLine(0, 0, self.width(), 0)
                painter.drawLine(self.width(), 0, self.width(), self.height())
                painter.drawLine(self.width(), self.height(), 0, self.height())
                painter.drawLine(0, self.height(), 0, 0)
        finally:
            painter.end()

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if (self.app.timeline_manager.current_frame != self.index):
            self.app.timeline_manager.current_frame = self.index
            self.app.main_window.canvas_pane.present(self.app.layer_manager.composite(
                self.index, self.app.timeline_manager.current_time))
