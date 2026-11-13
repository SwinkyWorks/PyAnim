from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from app import App
from PySide6.QtWidgets import QMenu


class PluginData:
    def __init__(
        self,
        name: str | None = None,
        author: str | None = None,
        version: str | None = None,
        description: str | None = None,
        icon: str | None = None,
        depends_on: list[str] | str | None = None,
        has_edit_menu: object | None = None,
        help_page: str | None = None,
        base_path: str = ""
    ):
        self.name = name if name != None else "Untitled Plugin"
        self.author = author if author != None else "Anonymous"
        self.version = version
        self.description = description
        self.icon = icon
        self.depends_on = depends_on if depends_on is list else (
            [depends_on] if depends_on is str else [])
        self.has_edit_menu = has_edit_menu != False
        self.help_page = help_page
        self.plugin_instance: BasePlugin | None = None
        self.base_path = base_path

    def __str__(self):
        return f"PluginData(name=\"{self.name}\", author=\"{self.author}\", version=\"{self.version}\", description=\"{self.description}\", icon=\"{self.icon}\", depends_on={self.depends_on}, has_edit_menu={self.has_edit_menu}, help_page=\"{self.help_page}\", base_path=\"{self.base_path}\")"


class BasePlugin:
    def __init__(self, app: "App", plugin_data: PluginData):
        self.app = app
        self.plugin_data = plugin_data
        super().__init__()

    def register_types(self):
        """Called on load. Register all custom layer and tool types."""
        ...

    def get_edit_menu(self) -> QMenu | None:
        """Return a QMenu that contains the stuff you want your plugin to do."""
        return None
