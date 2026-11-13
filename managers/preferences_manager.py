import json
from typing import TYPE_CHECKING, Any
from core.paths import user_data_path
if TYPE_CHECKING:
    from app import App


class PreferencesManager:
    """Loads, saves and exposes user preferences, stored in `preferences.json` next to `main.py`."""

    #: Every preference the app knows about, with the value used when the file lacks it.
    DEFAULTS: dict[str, Any] = {
        "new_objects_visible_in_all_frames": False,
    }

    def __init__(self, app: "App"):
        self.app = app
        self.path = user_data_path("preferences.json")
        self.values: dict[str, Any] = dict(self.DEFAULTS)
        self.load()

    def load(self) -> None:
        """Read `preferences.json`, falling back to defaults for anything missing or malformed."""
        if self.path.exists():
            try:
                data = json.loads(self.path.read_text())
            except (json.JSONDecodeError, OSError) as e:
                print(
                    f"PreferencesManager: could not read {self.path.name} ({e}), using defaults.")
                data = {}
            if isinstance(data, dict):
                for key in self.DEFAULTS:
                    if key in data:
                        self.values[key] = data[key]

    def save(self) -> None:
        """Write the current preferences back to disk."""
        try:
            self.path.write_text(json.dumps(self.values, indent=4) + "\n")
        except OSError as e:
            print(
                f"PreferencesManager: could not save {self.path.name} ({e}).")

    def get(self, key: str) -> Any:
        return self.values.get(key, self.DEFAULTS.get(key))

    def set(self, key: str, value: Any) -> None:
        self.values[key] = value
        self.save()

    @property
    def new_objects_visible_in_all_frames(self) -> bool:
        """When True, newly created objects are visible on every frame instead of only the frame they were made on."""
        return bool(self.get("new_objects_visible_in_all_frames"))

    @new_objects_visible_in_all_frames.setter
    def new_objects_visible_in_all_frames(self, value: bool) -> None:
        self.set("new_objects_visible_in_all_frames", bool(value))
