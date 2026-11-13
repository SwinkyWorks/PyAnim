from core.base_plugin import BasePlugin, PluginData
from core.base_tool import BaseTool
from core.base_object import BaseObject
from core.base_layer import BaseLayer, ShaderLayer
from core.properties import Property
from core.vectors import Vec2, Vec3
from typing import TYPE_CHECKING
from pathlib import Path
from core.paths import seed_user_dir, is_frozen
if TYPE_CHECKING:
    from app import App
import json


class ToolManager:
    #: Where to point people for plugin-creation help. There is no bundled
    #: `help/` copy in a frozen build, so this has to be somewhere reachable.
    DOCS_URL = "https://github.com/SwinkyWorks/PyAnim"

    def __init__(self, app: "App"):
        self.app = app
        self.plugins: dict[str, PluginData] = {}
        self.tools: list[BaseTool] = []
        if is_frozen():
            # Plugins are hot-swappable Python the user can edit, so they live
            # in a writable per-user dir seeded once from the bundle.
            self.plugins_dir = seed_user_dir("plugins")
        else:
            self.plugins_dir = Path(__file__).parent.parent / "plugins"
        self.plugins_dir.mkdir(parents=True, exist_ok=True)
        self.actively_adding_plugins: list[str] = []
        self.shared_namespace: dict[str, type] = {
            "BasePlugin": BasePlugin,
            "BaseTool": BaseTool,
            "BaseLayer": BaseLayer,
            "ShaderLayer": ShaderLayer,
            "BaseObject": BaseObject,
            "Property": Property,
            "Vec2": Vec2,
            "Vec3": Vec3
        }

    def init(self):
        for plugin in self.plugins_dir.iterdir():
            # Finder leaves .DS_Store behind (including in the seeded plugin
            # dir of a frozen build), and that is not a broken plugin.
            if plugin.name.startswith("."):
                continue
            if plugin.is_dir():
                self.add_plugin(plugin.name, True)
            else:
                print(
                    f"The file {plugin} cannot be registered as a plugin! See {self.DOCS_URL} for plugin creation help.")

    def add_plugin(self, plugin_name: str, delete_on_missing_plugin: bool) -> bool:
        if plugin_name in self.plugins:
            return True
        if plugin_name in self.actively_adding_plugins:
            raise RecursionError(
                f"Plugin {plugin_name} is already actively being registered!")
        if (self.app.logging):
            print(
                f"Loading plugin {plugin_name}...")
        self.actively_adding_plugins.append(plugin_name)
        plugin_dir = self.plugins_dir / plugin_name
        json_path = plugin_dir / "tool.json"

        if not json_path.exists():
            json_path = plugin_dir / "plugin.json"

            if not json_path.exists():
                raise FileNotFoundError(f"No tool.json in {plugin_dir}")

        info: dict = json.loads(json_path.read_text())
        if ("depends_on" in info):
            for other_plugin_name in info["depends_on"]:
                if other_plugin_name not in self.plugins:
                    if (self.plugins_dir / other_plugin_name).exists():
                        if not self.add_plugin(other_plugin_name, delete_on_missing_plugin):
                            print(
                                f"This plugin ({plugin_name}) has a missing dependancy {other_plugin_name}! Deleting plugin...")
                            self.delete_plugin(plugin_name)
                            return False
                    elif delete_on_missing_plugin:
                        print(
                            f"This plugin ({plugin_name}) has a missing dependancy {other_plugin_name}! Deleting plugin...")
                        self.delete_plugin(plugin_name)
                        return False
                    else:
                        self.download_plugin(other_plugin_name)
        entry_path: Path = plugin_dir / info["entry"]  # e.g. "tool.py"

        code = entry_path.read_text()
        plugin_namespace = {**self.shared_namespace}  # ** unpacks a dict

        # I am so happy you're able to add a namespace for an exec :)
        exec(code, plugin_namespace)

        self.shared_namespace.update(plugin_namespace)
        PluginClass = plugin_namespace["PLUGIN_CLASS"]

        info_id = info["id"]
        info.pop("id")
        info.pop("entry")
        info["base_path"] = plugin_dir.as_posix()
        new_plugin_data = PluginData(**info)
        plugin_instance: BasePlugin = PluginClass(self.app, new_plugin_data)
        plugin_instance.register_types()
        new_plugin_data.plugin_instance = plugin_instance
        self.plugins[info_id] = new_plugin_data
        self.actively_adding_plugins.remove(plugin_name)

        return True

    def register_tool(self, plugin: BasePlugin, tool_type: type):
        if not issubclass(tool_type, BaseTool):
            raise ValueError(f"\"{tool_type.__name__}\" is not a layer type!")
        self.tools.append(tool_type(app=self.app, plugin=plugin))
        self.app.main_window.populate_toolbar(self.tools)

    def _plugins_with_value(self, attr: str):
        new_list: list[str] = []
        for key in self.plugins:
            if getattr(self.plugins[key], attr) != None:
                new_list.append(key)
        return new_list

    @property
    def plugins_with_edit_menus(self) -> list[str]:
        return self._plugins_with_value("has_edit_menu")

    @property
    def plugins_with_help_pages(self) -> list[str]:
        return self._plugins_with_value("help_page")

    def delete_plugin(self, plugin_name: str):
        pass

    def download_plugin(self, plugin_name: str):
        pass
