from os import environ

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication
from app import App

qapplication = QApplication([])
app = App()

# `build.py --test` sets this to verify the frozen bundle really comes up: it
# enters the normal event loop, requires a visible window, then self-terminates
# instead of blocking forever.
if environ.get("PYANIM_SMOKE_TEST") == "1":
    smoke_result = {"ok": False, "windows": 0}

    def smoke_check() -> None:
        visible = [w for w in qapplication.topLevelWidgets()
                   if w.isVisible() and w.width() > 0]
        smoke_result["windows"] = len(visible)
        smoke_result["ok"] = bool(visible)
        qapplication.quit()

    QTimer.singleShot(2000, smoke_check)
    qapplication.exec()

    print(f"Smoke test: {smoke_result['windows']} visible top-level window(s).")
    if not smoke_result["ok"]:
        print("Smoke test FAILED: the event loop ran but no window was shown.")
        raise SystemExit(1)
    print("Smoke test: event loop ran and exited cleanly.")
    raise SystemExit(0)

qapplication.exec()
