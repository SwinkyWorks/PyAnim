"""Frozen-aware path resolution.

When PyInstaller freezes the app, read-only resources (images, help pages,
bundled plugins) live in the bundle (`sys._MEIPASS`), while anything the user
owns or edits (preferences, hot-swappable plugins) lives in a writable
per-user directory. In a normal source checkout both resolve to the project
root so development behaviour is unchanged.
"""
import shutil
import sys
from pathlib import Path

APP_NAME = "PyAnim"


def is_frozen() -> bool:
    """True when running from a PyInstaller bundle."""
    return bool(getattr(sys, "frozen", False))


def project_root() -> Path:
    """The repo root in development, or the bundle's resource dir when frozen."""
    if is_frozen():
        return Path(getattr(sys, "_MEIPASS", Path(sys.executable).parent))
    return Path(__file__).resolve().parent.parent


def resource_path(*parts: str) -> Path:
    """A read-only bundled resource (images, help, default plugins)."""
    return project_root().joinpath(*parts)


def user_data_root() -> Path:
    """A writable directory the user owns for preferences and plugins."""
    if is_frozen():
        if sys.platform == "darwin":
            base = Path.home() / "Library" / "Application Support" / APP_NAME
        elif sys.platform.startswith("win"):
            base = Path.home() / "AppData" / "Roaming" / APP_NAME
        else:
            base = Path.home() / ".local" / "share" / APP_NAME
    else:
        base = project_root()
    base.mkdir(parents=True, exist_ok=True)
    return base


def user_data_path(*parts: str) -> Path:
    """A writable per-user file/directory (preferences.json, plugins)."""
    return user_data_root().joinpath(*parts)


def seed_user_dir(name: str) -> Path:
    """Copy a bundled resource directory into the user dir on first run.

    Returns the user-side path; if it already exists it is left untouched so
    user edits survive later launches.
    """
    target = user_data_path(name)
    bundled = resource_path(name)
    if not target.exists() and bundled.exists():
        shutil.copytree(bundled, target)
    return target
