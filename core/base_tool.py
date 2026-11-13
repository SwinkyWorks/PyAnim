from core.base_event_handler import BaseEventHandler
from core.properties import HasProperties
from core.base_plugin import BasePlugin
from PySide6.QtGui import QIcon
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from app import App


class BaseTool(HasProperties, BaseEventHandler):
    def __init__(self, app: "App", plugin: BasePlugin):
        self.plugin = plugin
        super().__init__(app)
        self.is_tool = True

    @property
    def icon(self) -> QIcon:
        """Return a QIcon to be shown for this tool on the toolbar."""
        return QIcon()
