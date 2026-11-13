from PySide6.QtGui import QColor
from core.circuit.port import InputPort, OutputPort
from core.action import Action
from core.vectors import Vec3
from core.interpolation_modes import BaseInterpolation, StaticInterpolation
from typing import Callable, Any, TYPE_CHECKING, cast
if TYPE_CHECKING:
    from app import App
import math


def bound(min_value, max_value, value: Any):
    if hasattr(value.__class__, "bound") and callable(value.__class__.bound):
        return value.__class__.bound(min_value, max_value, value)
    if min_value == None and max_value == None:
        return value
    try:
        if min_value is not None and value < min_value:
            return min_value
        if max_value is not None and value > max_value:
            return max_value
        return value
    except TypeError:
        if isinstance(value, str) and isinstance(min_value, int) and isinstance(max_value, int):
            return value[:max_value] if (max_value != None and len(value) > max_value) else value if (min_value == None or len(value) > min_value) else value + " " * (min_value - len(value))


class DynamicValue[T]:
    def __init__(self, app: "App", default: T, min_value: Any = None, max_value: Any = None, bounder: Callable[[Any, Any, T], T] | None = None, name: str = "Unnamed Value"):
        self.app = app
        self.default = default
        self._min = min_value
        self._max = max_value
        self._bounder: Callable[[Any, Any, Any],
                                Any] = bounder if bounder != None else bound
        self.value_type: type[T] = type(default)
        self._circuit_source: InputPort[T] | None = None
        self._on_modify: Action = Action(Any)
        self._on_keyframe_modify: Action = Action(Any)
        self._keyframes: list[
            tuple[
                int,
                T,
                BaseInterpolation
            ]
        ] = []
        self._is_keyframed: bool = False
        self._static_value: T = default
        self._current_value: T = default
        self._keyframe_value: T = default
        self.name = name
        self.app.timeline_manager.on_time_change += self.resolve
        self.app.timeline_manager.on_new_frame += self.on_new_frame
        self.app.timeline_manager.on_duplicated_frame += self.on_duplicated_frame
        self.app.timeline_manager.on_deleted_frame += self.on_deleted_frame
        self.app.timeline_manager.on_moved_frame += self.on_moved_frame

    @property
    def is_keyframed(self) -> bool:
        return self._is_keyframed

    @is_keyframed.setter
    def is_keyframed(self, value: bool):
        if self._is_keyframed != value:
            self.app.timeline_manager.add_keyframed_value(
                self) if value else self.app.timeline_manager.delete_keyframed_value(self)
        self._is_keyframed = value

    @property
    def current_value(self) -> T:
        return self._current_value

    @current_value.setter
    def current_value(self, value: T):
        if (self._circuit_source != None):
            return
        if (not self.is_keyframed):
            new_value = self._bounder(self._min, self._max, value)
            self._static_value = new_value
        else:
            self.create_keyframe_at(
                self.app.timeline_manager.current_frame, value)

        self.resolve(self.app.timeline_manager.current_frame)

    @property
    def keyframe_value(self) -> T:
        return self._keyframe_value

    @keyframe_value.setter
    def keyframe_value(self, value: T):
        if (self._circuit_source != None):
            return
        if (not self.is_keyframed):
            new_value = self._bounder(self._min, self._max, value)
            self._static_value = new_value
        else:
            self.create_keyframe_at(
                self.app.timeline_manager.current_frame, value)

        self.resolve(self.app.timeline_manager.current_frame)

    @property
    def is_circuit_driven(self) -> bool:
        return self._circuit_source is not None

    def resolve(self, frame: int):
        old_values = (self._current_value, self._keyframe_value)
        self._current_value = self.get_value_at(frame, False)
        self._keyframe_value = self.get_value_at(frame, True)

        if (self._current_value, self._keyframe_value) != old_values:
            self._on_modify(self._current_value)
            self._on_keyframe_modify(self._keyframe_value)

    def on_new_frame(self, frame: int):
        for i, keyframe in enumerate(self._keyframes):
            if (keyframe[0] > frame):
                self._keyframes[i] = (
                    keyframe[0] + 1, keyframe[1], keyframe[2])

    def on_duplicated_frame(self, frame: int):
        for i, keyframe in enumerate(self._keyframes[:]):
            if (keyframe[0] > frame):
                self._keyframes[i] = (
                    keyframe[0] + 1, keyframe[1], keyframe[2])
            elif (keyframe[0] == frame):
                self._keyframes.append(
                    (frame + 1, keyframe[1], keyframe[2].duplicate()))
        self._keyframes.sort(key=lambda kf: kf[0])

    def on_deleted_frame(self, frame: int):
        for i, keyframe in reversed(list(enumerate(self._keyframes))):
            if (keyframe[0] > frame):
                self._keyframes[i] = (
                    keyframe[0] - 1, keyframe[1], keyframe[2])
            elif (keyframe[0] == frame):
                self._keyframes.pop(i)

    def on_moved_frame(self, a: int, b: int):
        if a == b:
            return
        for i, keyframe in enumerate(self._keyframes):
            if (keyframe[0] == a):
                self._keyframes[i] = (b, keyframe[1], keyframe[2])
            elif (a > b and keyframe[0] >= b and keyframe[0] < a):
                self._keyframes[i] = (
                    keyframe[0] + 1, keyframe[1], keyframe[2])
            elif (b > a and keyframe[0] > a and keyframe[0] <= b):
                self._keyframes[i] = (
                    keyframe[0] - 1, keyframe[1], keyframe[2])

    def get_value_at_time(self, time: float, get_keyframe: bool) -> T:
        if self._circuit_source:
            new_value = self._circuit_source.get_value()
            return self._bounder(self._min, self._max, new_value)
        elif self._keyframes:
            kfs = sorted(self._keyframes, key=lambda t: t[0])
            if len(kfs) == 1:
                return self._bounder(self._min, self._max, kfs[0][1])

            first = kfs[0]
            first_time = self.app.timeline_manager.time_at_frame(first[0])
            if time <= first_time:
                return self._bounder(self._min, self._max, first[1])

            last = kfs[-1]
            last_time = self.app.timeline_manager.time_at_frame(last[0])
            if time >= last_time:
                return self._bounder(self._min, self._max, last[1])

            for a, b in zip(kfs, kfs[1:]):
                lower = self.app.timeline_manager.time_at_frame(a[0])
                upper = self.app.timeline_manager.time_at_frame(b[0])
                if time == upper:
                    # Purely for allowing you to have a keyframe outside the graph without it snapping back immediately after.
                    return b[1] if get_keyframe else self._bounder(self._min, self._max, b[1])
                if time == lower:
                    return a[1] if get_keyframe else self._bounder(self._min, self._max, b[1])
                if time < upper:
                    v = cast(T, a[2].interpolate(
                        a[1], b[1], time - lower, upper - lower))
                    return self._bounder(self._min, self._max, v)

            return self._bounder(self._min, self._max, last[1])
        else:
            return self._bounder(self._min, self._max, self._static_value)

    def get_value_at(self, frame: int, get_keyframe: bool) -> T:
        return self.get_value_at_time(self.app.timeline_manager.time_at_frame(frame), get_keyframe)

    def has_keyframe_at(self, frame: int) -> bool:
        return any(kf[0] == frame for kf in self._keyframes)

    def create_keyframe_at(self, frame: int, value: T):
        if (self.has_keyframe_at(frame)):
            idx = [i for i, x in enumerate(
                self._keyframes) if x[0] == self.app.timeline_manager.current_frame][0]
            self._keyframes[idx] = (
                frame, value, self._keyframes[idx][2].duplicate())
        elif (len(self._keyframes) == 0):
            self._keyframes.append((frame, value, StaticInterpolation()))
        else:
            closest_value = min(
                self._keyframes, key=lambda t: abs(t[0] - frame))
            self._keyframes.append(
                (frame, value, closest_value[2].duplicate()))
        self.is_keyframed = True
        self._on_modify(value)
        self._on_keyframe_modify(value)

    def delete_keyframe_at(self, frame: int):
        self._keyframes = [kf for kf in self._keyframes if kf[0] != frame]
        self.resolve(self.app.timeline_manager.current_frame)

    def on_destroy(self):
        self.is_keyframed = False
        if self.resolve in self.app.timeline_manager.on_time_change:
            self.app.timeline_manager.on_time_change -= self.resolve
        if self.on_new_frame in self.app.timeline_manager.on_new_frame:
            self.app.timeline_manager.on_new_frame -= self.on_new_frame
        if self.on_duplicated_frame in self.app.timeline_manager.on_duplicated_frame:
            self.app.timeline_manager.on_duplicated_frame -= self.on_duplicated_frame
        if self.on_deleted_frame in self.app.timeline_manager.on_deleted_frame:
            self.app.timeline_manager.on_deleted_frame -= self.on_deleted_frame
        if self.on_moved_frame in self.app.timeline_manager.on_moved_frame:
            self.app.timeline_manager.on_moved_frame -= self.on_moved_frame
