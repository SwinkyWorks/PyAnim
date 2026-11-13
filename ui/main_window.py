# QMainWindow, menu bar, dockable panels
from PySide6.QtCore import QSize, Qt
from PySide6.QtWidgets import QDialog, QDialogButtonBox, QFormLayout, QMainWindow, QSpinBox, QTabWidget, QSplitter, QWidget, QTreeWidgetItem, QMenu, QAbstractItemView, QScrollArea, QVBoxLayout, QLayout, QToolButton, QSizePolicy, QCheckBox
from PySide6.QtGui import QAction, QMouseEvent
from ui.canvas import Canvas
from ui.keyframe_widget import KeyframeWidget
from ui.layer_tree_widget import LayerTreeWidget
from ui.timeline_widget import TimelineWidget
from core.base_object import BaseObject
from core.base_layer import BaseLayer
from core.base_tool import BaseTool
from core.properties import Property
from core.vectors import Vec2
from core.pyside6_helpers import clear_layout
from core.paths import resource_path
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from app import App
from functools import partial
import webbrowser


class MainWindow(QMainWindow):
    def __init__(self, app: "App"):
        super().__init__()
        self.app = app

        self.resize(1200, 800)
        self.setMinimumSize(800, 600)
        self.edit_plugins: list[QMenu] = []
        self.help_plugins: list[QAction] = []

        if (self.app.logging):
            print("Creating main window")

        self.tab_widget = QTabWidget(self)
        if True:  # tab_widget
            self.main_tab = QSplitter(
                Qt.Orientation.Vertical,
                self.tab_widget
            )
            self.tab_widget.addTab(self.main_tab, "Main")
            if True:  # mainTab
                self.main_top_splitter = QSplitter(
                    Qt.Orientation.Horizontal,
                    self.main_tab
                )
                self.main_tab.addWidget(self.main_top_splitter)
                if True:  # mainTopSplitter
                    self.tool_bar = CustomToolbar(app, self.main_top_splitter)
                    tool_bar_layout = QVBoxLayout()
                    self.tool_bar.setLayout(tool_bar_layout)
                    tool_bar_layout.setContentsMargins(0, 0, 0, 0)
                    tool_bar_layout.setSpacing(0)
                    tool_bar_layout.setAlignment(
                        Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignCenter)
                    self.tool_bar.setFixedWidth(40)
                    self.main_top_splitter.addWidget(self.tool_bar)
                    self.canvas_pane = Canvas(app, self.main_top_splitter)
                    self.main_top_splitter.addWidget(self.canvas_pane)
                    self.prop_layerSplit = QSplitter(
                        Qt.Orientation.Vertical,
                        self.main_top_splitter
                    )
                    # Default is 1:1
                    self.main_top_splitter.addWidget(self.prop_layerSplit)
                    if True:  # prop_layerSplit
                        self.properties_scroll = QScrollArea(
                            self.prop_layerSplit)
                        self.prop_layerSplit.addWidget(self.properties_scroll)
                        if True:  # properties_scroll
                            self.properties_pane = QWidget(
                                self.properties_scroll)
                            layout = QVBoxLayout()
                            self.properties_pane.setLayout(layout)
                            self.properties_scroll.setWidget(
                                self.properties_pane)
                            layout.setAlignment(Qt.AlignmentFlag.AlignTop)
                            self.properties_scroll.setWidgetResizable(True)
                        self.layers_pane = LayerTreeWidget(
                            app, self.prop_layerSplit)
                        self.prop_layerSplit.addWidget(self.layers_pane)
                        if True:  # layers_pane
                            self.layers_pane.setAcceptDrops(True)
                            self.layers_pane.setDropIndicatorShown(True)
                            self.layers_pane.setDragDropMode(
                                QAbstractItemView.DragDropMode.InternalMove)
                            self.layers_pane.itemExpanded.connect(
                                self._on_layer_expanded)
                            self.layers_pane.itemCollapsed.connect(
                                self._on_layer_collapsed)
                        self.prop_layerSplit.setSizes([
                            480 - int(self.tab_widget.sizeHint().height()*2/5),
                            480 - int(self.tab_widget.sizeHint().height()*2/5)
                        ])
                self.main_top_splitter.setSizes(
                    [40, 812, 348]
                )  # Toolbar is 40px
                self.main_top_splitter.setStretchFactor(0, 0)
                self.main_top_splitter.setStretchFactor(1, 7)
                self.main_top_splitter.setStretchFactor(2, 3)
                self.timeline_tabber = QTabWidget(self.main_tab)
                self.timeline_scroll = QScrollArea(self.timeline_tabber)
                self.timeline_tabber.addTab(self.timeline_scroll, "Timeline")
                self.timeline_scroll.setVerticalScrollBarPolicy(
                    Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
                self.timeline_scroll.setHorizontalScrollBarPolicy(
                    Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
                self.timeline_widget = TimelineWidget(
                    self.app, self.timeline_scroll)
                self.timeline_scroll.setWidget(self.timeline_widget)
                self.timeline_scroll.setWidgetResizable(True)
                self.timeline_scroll.setMinimumHeight(100)
                self.keyframe_widget = KeyframeWidget(
                    self.app, self.timeline_tabber)
                self.timeline_tabber.addTab(self.keyframe_widget, "Keyframes")
                self.main_tab.addWidget(self.timeline_tabber)
            # Canvas/toolbar/properties/layers get 4 parts
            self.main_tab.setSizes(
                [960 - int(self.tab_widget.sizeHint().height()*4/5),
                 240 - int(self.tab_widget.sizeHint().height()/5)]
            )
            self.main_tab.setStretchFactor(0, 4)
            self.main_tab.setStretchFactor(1, 1)  # Timeline gets 1 part
            self.circuit_board_tab = QSplitter(
                Qt.Orientation.Horizontal,
                self.tab_widget
            )
            self.tab_widget.addTab(self.circuit_board_tab, "Circuit Board")

            if True:  # circuitBoardTab
                self.circuit_board_pane = QWidget(self.circuit_board_tab)
                self.circuit_board_tab.addWidget(self.circuit_board_pane)

                self.circuit_board_properties_pane = QWidget(
                    self.circuit_board_tab)
                self.circuit_board_tab.addWidget(
                    self.circuit_board_properties_pane)

            self.circuit_board_tab.setStretchFactor(0, 7)
            self.circuit_board_tab.setStretchFactor(1, 3)

        self.setCentralWidget(self.tab_widget)

        if (self.app.logging):
            print("Creating menu bar")

        menu_bar = self.menuBar()
        menu_bar.setNativeMenuBar(False)

        if True:  # Menu bar
            self.file_menu = menu_bar.addMenu("File")
            if True:  # File menu
                self.file_menu.addAction(
                    "New project",
                    self.app.save_manager.onNewProject
                )
                self.file_menu.addAction(
                    "Open...",
                    self.app.save_manager.onOpenProject
                )

                self.file_menu.addSeparator()

                # Will redirect back to onSaveAs if has not been saved yet
                self.file_menu.addAction(
                    "Save",
                    "Ctrl+S",
                    self.app.save_manager.onSave
                )
                self.file_menu.addAction(
                    "Save as...",
                    "Ctrl+Shift+S",
                    self.on_save_as
                )

                self.file_menu.addSeparator()

                self.file_menu.addAction(
                    "Resize canvas...",
                    self.resize_canvas
                )

                self.file_menu.addSeparator()

                self.file_menu.addAction(
                    "Preferences...",
                    "Ctrl+,",
                    self.open_preferences
                )

                self.file_menu.addSeparator()

                self.export_menu = self.file_menu.addMenu("Export")
                self.export_menu.addAction(
                    "MP4",
                    self.app.export_manager.on_export_as_mp4
                )
                self.export_menu.addAction(
                    "GIF",
                    self.app.export_manager.on_export_as_gif
                )
                self.export_menu.addAction(
                    "Animated WEBP",  # "animated" because WEBP can be both an image and an animation
                    self.app.export_manager.on_export_as_webp
                )
                self.export_sequence_menu = self.export_menu.addMenu(
                    "Image sequence")
                self.export_sequence_png_menu = self.export_sequence_menu.addMenu(
                    "PNG")
                self.export_sequence_png_menu.addAction(
                    "Transparent background",
                    partial(
                        self.app.export_manager.on_export_as_image_sequence, "PNG", True)
                )
                self.export_sequence_png_menu.addAction(
                    "Opaque background",
                    partial(
                        self.app.export_manager.on_export_as_image_sequence, "PNG", False)
                )
                self.export_sequence_menu.addAction(
                    "JPG",
                    partial(
                        self.app.export_manager.on_export_as_image_sequence, "JPG", False)
                )
                self.export_sequence_webp_menu = self.export_sequence_menu.addMenu(
                    "Animated WEBP")
                self.export_sequence_webp_menu.addAction(
                    "Transparent background",
                    partial(
                        self.app.export_manager.on_export_as_image_sequence, "WEBP", True)
                )
                self.export_sequence_webp_menu.addAction(
                    "Opaque background",
                    partial(
                        self.app.export_manager.on_export_as_image_sequence, "WEBP", False)
                )

            self.edit_menu = menu_bar.addMenu("Edit")
            if True:
                self.new_layer_menu = self.edit_menu.addMenu("New Layer")
                self.new_layer_menu.aboutToShow.connect(
                    self.populate_new_layer_menu
                )
                self.new_frame_menu = self.edit_menu.addAction(
                    "New frame",
                    ";",
                    self.app.timeline_manager.create_frame
                )

                self.edit_menu.addSeparator()
                self.duplicate_object_menu = self.edit_menu.addAction(
                    "Duplicate Selected Object",
                    "Ctrl+D",
                    self.app.input_manager.duplicate_selected_object
                )
                self.duplicate_frame_menu = self.edit_menu.addAction(
                    "Duplicate Selected Frame",
                    "Ctrl+Alt+D",
                    self.app.timeline_manager.duplicate_frame
                )

                self.edit_menu.addSeparator()
                self.delete_layer_menu = self.edit_menu.addAction(
                    "Delete Selected Object",
                    "Backspace",
                    self.app.input_manager.delete_selected_object
                )
                self.delete_frame_menu = self.edit_menu.addAction(
                    "Delete Selected Frame",
                    "Alt+Backspace",
                    self.app.timeline_manager.delete_frame
                )

                self.edit_menu.addSeparator()

                self.delete_frame_menu = self.edit_menu.addAction(
                    "Move Selected Frame Backward",
                    "Shift+Left",
                    self.app.timeline_manager.move_frame_backward
                )
                self.delete_frame_menu = self.edit_menu.addAction(
                    "Move Selected Frame Forward",
                    "Shift+Right",
                    self.app.timeline_manager.move_frame_forward
                )

                self.edit_menu.addSeparator()

                self.edit_menu.aboutToShow.connect(
                    self.populate_edit_menu
                )
            self.view_menu = menu_bar.addMenu("View")
            if True:
                self.show_menu = self.view_menu.addMenu("Show")
                if True:
                    # Add the panels later :P
                    # Won't be checked from the start
                    self.show_menu.addAction(
                        "Show onion skinning",
                        "Ctrl+O",
                        self.app.layer_manager.toggle_onion_skinning
                    ).setCheckable(True)
                    self.show_menu.addAction(
                        # Ditto
                        "All layers", self.app.layer_manager.toggle_show_all_layers
                    ).setCheckable(True)
                    self.specific_layers_menu = self.show_menu.addMenu(
                        "Specific layers"
                    )
                    self.specific_layers_menu.aboutToShow.connect(
                        self.populate_hide_layers_menu
                    )
                self.view_menu.addAction(
                    "Preview",
                    self.preview
                )

                self.view_menu.addAction(
                    "Reset view",
                    "=",
                    self.canvas_pane.reset_scroll
                )
                self.view_menu.addSeparator()
                self.view_menu.addAction(
                    "Next Frame",
                    "Right",
                    self.app.timeline_manager.next_frame
                )
                self.view_menu.addAction(
                    "Previous Frame",
                    "Left",
                    self.app.timeline_manager.prev_frame
                )
            self.plugins_menu = menu_bar.addMenu("Plugins")
            if True:
                self.plugins_menu.addAction(
                    "Find new plugins...",
                    self.on_open_plugins_menu
                )
                self.delete_plugins_menu = self.plugins_menu.addMenu(
                    "Delete"
                )
                self.delete_plugins_menu.aboutToShow.connect(
                    self.populate_delete_plugins_menu
                )
            self.help_menu = menu_bar.addMenu("Help")
            if True:
                self.help_menu.addAction(
                    "Usage...",
                    self.on_open_usage_menu
                )
                self.help_menu.addAction(
                    "Documentation...",
                    self.on_open_documentation_menu
                )
                self.help_menu.aboutToShow.connect(
                    self.populate_help_menu
                )

        self.setUnifiedTitleAndToolBarOnMac(True)

        if (self.app.logging):
            print("Showing window")
        self.show()
        self.setWindowTitle("PyAnim")

    def on_save_as(self):
        pass  # Open up a screen overlay

    def preview(self):
        pass

    def on_open_plugins_menu(self):
        pass  # Open up a screen overlay

    def on_open_usage_menu(self):
        self.openURL(resource_path("help", "usage.html").as_uri())

    def on_open_documentation_menu(self):
        self.openURL(resource_path("help", "documentation.html").as_uri())

    def populate_new_layer_menu(self):
        self.new_layer_menu.clear()
        for name in self.app.layer_manager.registered_layer_types:
            self.new_layer_menu.addAction(
                name,
                partial(self.app.layer_manager.create_layer, name)
            )

    def populate_edit_menu(self):
        for menu in self.edit_plugins:
            self.edit_menu.removeAction(menu.menuAction())
        for name in self.app.tool_manager.plugins_with_edit_menus:
            plugin_instance = self.app.tool_manager.plugins[name].plugin_instance
            if (plugin_instance != None):
                new_menu = plugin_instance.get_edit_menu()
                if (new_menu != None):
                    self.edit_menu.addMenu(new_menu)
                    self.edit_plugins.append(new_menu)

    def populate_hide_layers_menu(self):
        self.specific_layers_menu.clear()
        for name in self.app.layer_manager.registered_layer_types:
            new_action = self.specific_layers_menu.addAction(
                name,
                partial(self.app.layer_manager.toggle_hide_specific_layers, name)
            )
            new_action.setCheckable(True)
            new_action.setChecked(
                not self.app.layer_manager.hide_specific_layers[name]
                if name in self.app.layer_manager.hide_specific_layers
                else True
            )

    def populate_delete_plugins_menu(self):
        self.delete_plugins_menu.clear()
        for name in self.app.tool_manager.plugins:
            self.delete_plugins_menu.addAction(
                self.app.tool_manager.plugins[name].name,
                partial(
                    self.app.tool_manager.delete_plugin,
                    name
                )
            )

    def populate_help_menu(self):
        for action in self.help_plugins:
            self.help_menu.removeAction(action)
        self.help_plugins.clear()
        for name in self.app.tool_manager.plugins_with_help_pages:
            self.help_plugins.append(
                self.help_menu.addAction(
                    self.app.tool_manager.plugins[name].name,
                    partial(
                        self.openURL,
                        self.app.tool_manager.plugins[name].help_page
                    )
                )
            )

    def populate_layers_menu(self):
        self.layers_pane.isUpdatingTree = True
        self.layers_pane.clear()
        selected_item: QTreeWidgetItem | None = None

        to_expand: list[QTreeWidgetItem] = []

        def add_layer_item(layer: BaseLayer):
            item = QTreeWidgetItem([layer.name])
            item.setData(0, Qt.ItemDataRole.UserRole, layer)
            if (layer == self.app.input_manager.selected_object):
                selected_item = item

            if layer.objects:
                objects_group = QTreeWidgetItem(
                    ["Objects"])
                objects_group.setData(
                    0, Qt.ItemDataRole.UserRole, "ObjectsContainer")
                objects_group.setData(1, Qt.ItemDataRole.UserRole, layer)
                if (self.layers_pane.selectedObjectsContainer == layer):
                    selected_item = objects_group
                for obj in reversed(layer.objects):
                    obj_item = QTreeWidgetItem(
                        [obj.name])
                    if (obj == self.app.input_manager.selected_object):
                        selected_item = obj_item
                    objects_group.addChild(obj_item)
                    obj_item.setData(0, Qt.ItemDataRole.UserRole, obj)
                item.addChild(objects_group)
                if (layer.objects_expanded):
                    to_expand.append(objects_group)

            for child_layer in reversed(layer.children):
                item.addChild(add_layer_item(child_layer))

            if layer.expanded:
                to_expand.append(item)

            return item

        for layer in reversed(self.app.layer_manager.layers):
            self.layers_pane.addTopLevelItem(add_layer_item(layer))

        for item in to_expand:
            item.setExpanded(True)

        if (selected_item != None):
            self.layers_pane.setCurrentItem(selected_item)

        self.layers_pane.isUpdatingTree = False

    def _on_layer_expanded(self, item: QTreeWidgetItem):
        layer: BaseLayer | str | BaseObject = item.data(
            0, Qt.ItemDataRole.UserRole)
        if isinstance(layer, BaseLayer):
            layer.expanded = True
        elif isinstance(layer, str):
            item.data(1, Qt.ItemDataRole.UserRole).objects_expanded = True

    def _on_layer_collapsed(self, item: QTreeWidgetItem):
        layer: BaseLayer | str | BaseObject = item.data(
            0, Qt.ItemDataRole.UserRole)
        if isinstance(layer, BaseLayer):
            layer.expanded = False
        elif isinstance(layer, str):
            item.data(1, Qt.ItemDataRole.UserRole).objects_expanded = False

    def openURL(self, url: str | None = None):
        webbrowser.open(url) if url != None else ""

    def populate_toolbar(self, tools: list[BaseTool]):
        layout = self.tool_bar.layout()
        if isinstance(layout, QLayout):
            clear_layout(layout)
            for tool in tools:
                icon = tool.icon
                button = QToolButton(
                    self.tool_bar, toolButtonStyle=Qt.ToolButtonStyle.ToolButtonIconOnly)
                layout.addWidget(button)
                button.setIcon(icon)
                button.setIconSize(QSize(25, 25))
                button.setAutoExclusive(True)
                button.clicked.connect(
                    partial(
                        self.app.input_manager.select_tool,
                        tool
                    )
                )
                button.setContentsMargins(0, 0, 0, 0)
                button.setStyleSheet(
                    "QToolButton { padding: 0px; margin: 0px; }")
                button.setSizePolicy(
                    QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
                button.setFixedWidth(30)
                button.setFixedHeight(30)

    def resize_canvas(self):
        dialog = ResizeCanvasDialog(
            width=self.app.layer_manager.size.width(),
            height=self.app.layer_manager.size.height(),
            parent=self
        )

        if dialog.exec() == QDialog.DialogCode.Accepted:
            width, height = dialog.size_values()
            self.app.layer_manager.size = QSize(width, height)
            self.app.layer_manager.update_layers()

    def switch_to_keyframe_widget(self, value: Property):
        self.timeline_tabber.setCurrentIndex(1)

    def open_preferences(self):
        dialog = PreferencesDialog(self.app.preferences_manager, parent=self)
        dialog.exec()


class CustomToolbar(QWidget):
    def __init__(self, app: "App", /, parent: QWidget | None = None) -> None:
        self.app = app
        super().__init__(parent)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        self.app.input_manager.select_tool(None)
        return super().mousePressEvent(event)


class ResizeCanvasDialog(QDialog):
    def __init__(self, width: int, height: int, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Resize Canvas")

        self.width_spin = QSpinBox()
        self.width_spin.setRange(1, 100_000)
        self.width_spin.setValue(width)

        self.height_spin = QSpinBox()
        self.height_spin.setRange(1, 100_000)
        self.height_spin.setValue(height)

        form = QFormLayout()
        form.addRow("Width:", self.width_spin)
        form.addRow("Height:", self.height_spin)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok
            | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(buttons)

    def size_values(self) -> tuple[int, int]:
        return self.width_spin.value(), self.height_spin.value()


class PreferencesDialog(QDialog):
    """A live-editing preferences dialog: each control writes through to the PreferencesManager as soon as it changes."""

    def __init__(self, preferences, parent=None):
        super().__init__(parent)
        self.preferences = preferences

        self.setWindowTitle("Preferences")

        self.visible_all_checkbox = QCheckBox(
            "New objects visible in all frames")
        self.visible_all_checkbox.setToolTip(
            "When off, a new object is only visible on the frame it was created on.")
        self.visible_all_checkbox.setChecked(
            preferences.new_objects_visible_in_all_frames)
        self.visible_all_checkbox.toggled.connect(
            self.on_visible_all_toggled)

        form = QFormLayout()
        form.addRow("Objects:", self.visible_all_checkbox)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.rejected.connect(self.reject)
        buttons.accepted.connect(self.accept)

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(buttons)

    def on_visible_all_toggled(self, checked: bool):
        self.preferences.new_objects_visible_in_all_frames = checked
