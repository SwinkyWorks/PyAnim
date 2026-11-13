#!/bin/bash
export QT_QPA_PLATFORM_PLUGIN_PATH="$(pwd)/.venv/lib/python3.12/site-packages/PySide6/Qt/plugins/platforms"
export QT_PLUGIN_PATH="$(pwd)/.venv/lib/python3.12/site-packages/PySide6/Qt/plugins"
exec uv run python main.py "$@"
