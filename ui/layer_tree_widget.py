from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QTreeWidget, QTreeWidgetItem, QAbstractItemView
from PySide6.QtGui import QDropEvent, QMouseEvent
from core.base_layer import BaseLayer
from core.base_object import BaseObject
from core.errors import LayerTamperedException
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from app import App


class LayerTreeWidget(QTreeWidget):
    def __init__(self, app: "App", parent: QWidget | None = None):
        super().__init__(parent)
        self.app = app
        self.itemSelectionChanged.connect(self.onItemSelectionChanged)
        self.isUpdatingTree = False
        self.selectedObjectsContainer: BaseLayer | None = None

    def dropEvent(self, event: QDropEvent):
        target_item = self.itemAt(event.position().toPoint())
        position = self.dropIndicatorPosition()

        dropping_onto_item = (
            target_item is not None and
            position == QAbstractItemView.DropIndicatorPosition.OnItem
        )
        dropping_into_item = (  # We need to also check for dropping next to an item that is within another layer
            target_item is not None and
            target_item.parent() is not None and
            (
                position == QAbstractItemView.DropIndicatorPosition.AboveItem or
                position == QAbstractItemView.DropIndicatorPosition.BelowItem
            )
        )

        source = self.selectedItems()[0] if self.selectedItems() else None
        new_parent_layer = None
        our_layer = None

        if dropping_into_item and target_item.parent():
            new_parent_layer = target_item.parent().data(0, Qt.ItemDataRole.UserRole)
        else:
            if dropping_onto_item:
                new_parent_layer = target_item.data(
                    0, Qt.ItemDataRole.UserRole)

        # Can we drop?
        if isinstance(source, QTreeWidgetItem) and isinstance((our_layer := source.data(0, Qt.ItemDataRole.UserRole)), BaseLayer):
            if event.source() is not self:
                event.ignore()
                return
            if dropping_onto_item or dropping_into_item:
                if not isinstance(new_parent_layer, BaseLayer) or not new_parent_layer.accepts_children():
                    event.ignore()
                    return
        else:
            event.ignore()
            return

        # Remove our layer from current position
        if source.parent() and isinstance((old_parent_layer := source.parent().data(0, Qt.ItemDataRole.UserRole)), BaseLayer):
            if our_layer in old_parent_layer.children:
                old_parent_layer.children.remove(our_layer)
            else:
                raise LayerTamperedException(
                    f"Layer no longer exists directly under parent \"{old_parent_layer.name}\"")
        else:
            if our_layer in self.app.layer_manager.layers:
                self.app.layer_manager.layers.remove(our_layer)
            else:
                raise LayerTamperedException(
                    f"Layer no longer exists as top-level layer")

        # Add our layer to new position
        if new_parent_layer:
            if dropping_onto_item:
                new_parent_layer.children.append(our_layer)
            if dropping_into_item:
                new_index = len(new_parent_layer.children) - \
                    target_item.parent().indexOfChild(target_item) - 1
                if position == QAbstractItemView.DropIndicatorPosition.AboveItem:
                    new_index += 1
                new_parent_layer.children.insert(new_index, our_layer)
        else:
            if position == QAbstractItemView.DropIndicatorPosition.OnViewport:
                self.app.layer_manager.layers.insert(0, our_layer)
            if position == QAbstractItemView.DropIndicatorPosition.AboveItem or position == QAbstractItemView.DropIndicatorPosition.BelowItem:
                new_index = len(self.app.layer_manager.layers) - \
                    self.indexOfTopLevelItem(target_item) - 1
                if position == QAbstractItemView.DropIndicatorPosition.AboveItem:
                    new_index += 1
                self.app.layer_manager.layers.insert(new_index, our_layer)

        super().dropEvent(event)
        self.app.layer_manager.update_layers()

    def isDropAllowed(self, target_item: QTreeWidgetItem):
        layer = target_item.data(0, Qt.ItemDataRole.UserRole)
        if layer == None:
            return True
        return layer.accepts_children()

    def onItemSelectionChanged(self):
        if (self.isUpdatingTree):
            return
        item = self.selectedItems()[0] if len(
            self.selectedItems()) > 0 else None
        data = item.data(0, Qt.ItemDataRole.UserRole) if item != None else None
        if data == "ObjectsContainer" and item != None:
            self.selectedObjectsContainer = item.data(
                1, Qt.ItemDataRole.UserRole)
            self.app.input_manager.selected_object = None
        else:
            self.selectedObjectsContainer = None
        if isinstance(data, (BaseObject, type(None))):
            self.app.input_manager.select_object(data)

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            index = self.indexAt(event.pos())
            if not index.isValid():
                self.clearSelection()
        super().mousePressEvent(event)


"""

dropping onto item: OnItem
dropping into item: (AboveItem or BelowItem) and item is within a layer

# Can we drop?
if our layer exists:
    if dropping onto item or dropping into item:
        if new parent layer accepts children:
            accept drop
        else:
            reject drop
    else:
        accept drop
else:
    reject drop

# Remove our layer from current position
if old parent layer exists:
    if our layer is in old parent layer:
        pop our layer from old parent layer
    else:
        throw error: layers shouldn't mess with other layers
else:
    if our layer is in layers list:
        pop our layer from layers list
    else:
        throw error: wtf happened?

# Add our layer to new position
if new parent layer exists:
    if dropping onto item:
        append our layer onto other layer's list
    if dropping into item:
        get new index
        add our layer into other layer's list at new index
else:
    if OnViewport:
        append our layer onto layer list
    if AboveItem or BelowItem:
        get new index
        add our layer onto layer list at new index

"""
