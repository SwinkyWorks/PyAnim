"""Headless check for the new object-visibility behaviour. Run with QT_QPA_PLATFORM=offscreen."""
import os
import sys

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication  # nopep8

app_qt = QApplication([])

from app import App  # nopep8
from core.base_object import BaseObject  # nopep8


class DummyPlugin:
    pass


app = App()
tm = app.timeline_manager
pm = app.preferences_manager

# Make sure we have enough frames to test with.
while tm.num_frames < 5:
    tm.create_frame()
tm.current_frame = 2

results = []


def check(label, condition):
    results.append((label, bool(condition)))
    print(f"{'PASS' if condition else 'FAIL'}: {label}")


# Preference off -> visible only on creation frame.
pm.new_objects_visible_in_all_frames = False
obj = BaseObject(app, DummyPlugin(), "Test Object")
check("visible on creation frame (2)", obj.is_visible_at(2))
check("hidden on frame 1", not obj.is_visible_at(1))
check("hidden on frame 3", not obj.is_visible_at(3))
check("hidden on frame 0", not obj.is_visible_at(0))
check("visible property is keyframed",
      obj.properties["visible"].dynamic_value.is_keyframed)

# Preference on -> visible everywhere, not keyframed.
pm.new_objects_visible_in_all_frames = True
obj_all = BaseObject(app, DummyPlugin(), "All Frames Object")
check("all-frames object visible on frame 0", obj_all.is_visible_at(0))
check("all-frames object visible on frame 4", obj_all.is_visible_at(4))
check("all-frames object not keyframed",
      not obj_all.properties["visible"].dynamic_value.is_keyframed)

# Layers stay visible everywhere.
layer = app.layer_manager.get_layer("FreeformLayer", True)
check("layer visible on frame 0", layer.is_visible_at(0))
check("layer visible on last frame", layer.is_visible_at(tm.num_frames - 1))
check("layer not keyframed",
      not layer.properties["visible"].dynamic_value.is_keyframed)

# Duplicating must not orphan keyframed values in the timeline manager.
pm.new_objects_visible_in_all_frames = False
before = len(tm.keyframed_values)
dup = obj.on_duplicate()
after = len(tm.keyframed_values)
check(
    f"duplicate adds exactly one keyframed value (before={before}, after={after})", after == before + 1)
check("duplicate is visible on frame 2", dup.is_visible_at(2))
check("duplicate hidden on frame 3", not dup.is_visible_at(3))

# The visible property should be registered in the timeline exactly once per keyframed object.
count = len([v for v in tm.keyframed_values if v.name == "Visible"])
# obj + dup
check(
    f"one 'Visible' registration per keyframed object (count={count})", count == 2)

failed = [label for label, ok in results if not ok]
print()
print(f"{len(results) - len(failed)}/{len(results)} checks passed")
sys.exit(1 if failed else 0)
