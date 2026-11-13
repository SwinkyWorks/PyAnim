from core.properties import HasProperties, Property
from core.dynamic_value import DynamicValue
from core.base_plugin import BasePlugin
from core.base_event_handler import BaseEventHandler
from typing import TYPE_CHECKING, Self
if TYPE_CHECKING:
    from app import App


class BaseObject(HasProperties, BaseEventHandler):
    def __init__(self, app: "App", plugin: BasePlugin, name: str = ""):
        super().__init__(app)
        self.plugin = plugin
        self.name = name
        self.deleted = False
        self.properties.add_property("visible",
                                     name="Visible",
                                     default=False
                                     )
        self.set_initial_visibility()

    @property
    def visible(self) -> bool:
        """Whether this object is visible on the frame currently being viewed."""
        return bool(self.properties["visible"].value)

    def is_visible_at(self, frame: int) -> bool:
        """Whether this object is visible on a specific frame. Use this when rendering, since the frame being drawn is not always the current frame."""
        return bool(self.properties["visible"].get_value_at(frame))

    def set_initial_visibility(self):
        """Decide where this object is visible when it is first created.
        \nWith `new_objects_visible_in_all_frames` enabled, the object is visible everywhere.
        \nOtherwise it is only visible on the frame it was created on: the creation frame gets a `True` keyframe, and the frames either side get `False` keyframes so static interpolation hides it again."""
        visible = self.properties["visible"]
        dynamic_value = visible.dynamic_value
        frame = self.app.timeline_manager.current_frame

        if self.app.preferences_manager.new_objects_visible_in_all_frames:
            dynamic_value.is_keyframed = False
            dynamic_value.current_value = True
            return

        dynamic_value.create_keyframe_at(frame, True)
        if frame > 0:
            dynamic_value.create_keyframe_at(frame - 1, False)
        if frame + 1 < self.app.timeline_manager.num_frames:
            dynamic_value.create_keyframe_at(frame + 1, False)
        dynamic_value._keyframes.sort(key=lambda kf: kf[0])

    def on_delete(self) -> bool | None:
        """Called when the user attempts to delete this object directly.
        \nReturn True to prevent the deletion.
        \nNote: This isn't an actual deletion. Look at [this](https://stackoverflow.com/questions/3013304/how-to-delete-every-reference-of-an-object-in-python) for the reason why."""
        return False

    def on_duplicate(self) -> Self | bool:
        """Called when the user attempts to duplicate this object directly.
        \nReturn True to prevent the duplication, or return a copy of this object."""
        obj = self.__class__(self.app, self.plugin, self.name + " (Copy)")
        # Constructing the copy registered its own properties with the timeline;
        # discard them properly before replacing them with clones of ours.
        for property in obj.properties.items():
            property.dynamic_value.on_destroy()
        obj.properties.clear()

        for property in self.properties.items():
            p = Property(self.app, property.id, property.name, property.dynamic_value.default, None,
                         property.dynamic_value._min, property.dynamic_value._max, property.dynamic_value._bounder)
            p.dynamic_value._static_value = property.dynamic_value._static_value
            p.dynamic_value._keyframes = [
                (p[0], p[1], p[2].duplicate()) for p in property.dynamic_value._keyframes]
            p.dynamic_value.is_keyframed = property.dynamic_value.is_keyframed
            obj.properties[property.id] = p

        return obj
