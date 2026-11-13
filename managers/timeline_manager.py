from core.base_plugin import BasePlugin
from core.dynamic_value import DynamicValue
from core.interpolation_modes import BaseInterpolation, register_interpolation_modes
from core.action import Action
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from app import App


def fps_to_frametime(fps: float) -> float:
    return 1.0/fps


def frametime_to_fps(frametime: float) -> float:
    return 1.0/frametime


class FrameData:
    def __init__(self, app: "App", frametime: float = 0.0, is_default: bool = True) -> None:
        self.app = app
        self._frametime = frametime
        self.is_default = is_default

    @property
    def frametime(self) -> float:
        return self.frametime if not self.is_default else self.app.timeline_manager.default_frametime

    @frametime.setter
    def frametime(self, value: float):
        self._frametime = value
        self.is_default = False

    @property
    def fps(self) -> float:
        return frametime_to_fps(self.frametime)

    @fps.setter
    def fps(self, value: float):
        self.frametime = fps_to_frametime(value)


class TimelineManager:
    def __init__(self, app: "App"):
        self.app = app
        self.frames: list[FrameData] = [FrameData(app)]
        self.default_frametime: float = 1/30
        self._current_time = 0.0
        self._current_frame = 0
        self.is_playing = False
        self._playing_time = 0.0
        self.on_time_change = Action(int)
        self.on_new_frame = Action(int)
        self.on_duplicated_frame = Action(int)
        self.on_deleted_frame = Action(int)
        self.on_moved_frame = Action(int, int)
        self.keyframed_values: list[DynamicValue] = []
        self.registered_interpolation_modes: dict[str,
                                                  tuple[BasePlugin, type[BaseInterpolation]]] = {}
        self._cumulative_times: list[float] | None = None

    def init_interpolation_modes(self):
        register_interpolation_modes(self.app)

    def _invalidate_cache(self):
        self._cumulative_times = None

    def _build_cache(self):
        times: list[float] = [0.0]
        for f in self.frames[:-1]:
            times.append(
                times[-1] + (f.frametime if not f.is_default else self.default_frametime))
        self._cumulative_times = times

    def _get_cumulative_time(self, frame: int) -> float:
        if self._cumulative_times is None:
            self._build_cache()
        assert self._cumulative_times is not None
        return self._cumulative_times[frame]

    def frame_at_time(self, frametime: float) -> int:
        # Binary search over cached cumulative times for exactness
        if self._cumulative_times is None:
            self._build_cache()
        assert self._cumulative_times is not None
        cum = self._cumulative_times
        lo, hi = 0, len(cum) - 1
        while lo < hi:
            mid = (lo + hi + 1) // 2
            if cum[mid] <= frametime:
                lo = mid
            else:
                hi = mid - 1
        # lo is the largest index where cumulative_time <= frametime
        # Check if frametime is within this frame's duration
        frame_dur = self.frames[lo].frametime if not self.frames[lo].is_default else self.default_frametime
        if frametime < cum[lo] + frame_dur:
            return lo
        # Edge case: frametime is exactly at a boundary or past the last frame
        if frametime == cum[lo]:
            return lo
        return min(lo + 1, len(self.frames) - 1)

    def time_at_frame(self, frame: int) -> float:
        return self._get_cumulative_time(frame)

    def register_interpolation_mode(self, plugin: BasePlugin, type: type[BaseInterpolation]):
        className = type.__name__
        self.registered_interpolation_modes[className] = (plugin, type)

    @property
    def current_time(self) -> float:
        return self.time_at_frame(self.current_frame)

    @current_time.setter
    def current_time(self, value: float):
        self._current_time = self.time_at_frame(f := self.frame_at_time(value))
        if (self._current_frame != f):
            self.on_time_change(f)
            self._current_frame = f

    @property
    def current_frame(self) -> int:
        return self.frame_at_time(self._current_time)

    @current_frame.setter
    def current_frame(self, value: int):
        self.current_time = self.time_at_frame(value)

    @property
    def playing_time(self) -> float:
        return self.time_at_frame(self.playing_frame)

    @playing_time.setter
    def playing_time(self, value: float):
        self._playing_time = self.time_at_frame(self.frame_at_time(value))

    @property
    def playing_frame(self) -> int:
        return self.frame_at_time(self._playing_time)

    @playing_frame.setter
    def playing_frame(self, value: int):
        self._playing_time = self.time_at_frame(value)

    @property
    def default_fps(self) -> float:
        return frametime_to_fps(self.default_frametime)

    @default_fps.setter
    def default_fps(self, value: float):
        self.default_frametime = fps_to_frametime(value)

    @property
    def num_frames(self) -> int:
        return len(self.frames)

    @property
    def max_time(self) -> float:
        current_max: float = 0.0
        for frame in self.frames:
            if (frame.is_default):
                current_max += self.default_frametime
            else:
                current_max += frame.frametime
        return current_max

    @property
    def average_time(self) -> float:
        return self.max_time / self.num_frames

    @property
    def time_tuple(self) -> tuple[int, float]:
        return self.current_frame, self._current_time

    def advance(self, dt: float):
        self.playing_time += dt
        return self.playing_frame, self.playing_time

    def create_frame(self):
        self.frames.insert(self.current_frame + 1, FrameData(self.app))
        self.on_new_frame(self.current_frame)
        self._invalidate_cache()
        self.current_frame += 1
        self.app.layer_manager.update_layers()

    def duplicate_frame(self):
        self.frames.insert(self.current_frame + 1, FrameData(self.app,
                           self.frames[self.current_frame].frametime, self.frames[self.current_frame].is_default))
        self.on_duplicated_frame(self.current_frame)
        self._invalidate_cache()
        self.current_frame += 1
        self.app.layer_manager.update_layers()

    def delete_frame(self):
        if (len(self.frames) < 2):
            return
        f = self.current_frame
        self.current_frame -= 1
        self.frames.pop(f)
        self.on_deleted_frame(f)
        self._invalidate_cache()
        self.app.layer_manager.update_layers()

    def next_frame(self):
        self._invalidate_cache()
        self.current_frame += 1
        self.app.layer_manager.update_layers()

    def move_frame_forward(self):
        if (self.current_frame < len(self.frames) - 1):
            f = self.frames.pop(self.current_frame)
            self.frames.insert(self.current_frame + 2, f)
            self.on_moved_frame(self.current_frame, self.current_frame + 1)
            self._invalidate_cache()
            self.current_frame += 1
            self.app.layer_manager.update_layers()

    def prev_frame(self):
        if self.current_frame > 0:
            self._invalidate_cache()
            self.current_frame -= 1
        self.app.layer_manager.update_layers()

    def move_frame_backward(self):
        if (self.current_frame > 0):
            f = self.frames.pop(self.current_frame)
            self.frames.insert(self.current_frame, f)
            self.on_moved_frame(self.current_frame, self.current_frame - 1)
            self._invalidate_cache()
            self.current_frame -= 1
            self.app.layer_manager.update_layers()

    def add_keyframed_value(self, value: DynamicValue):
        self.keyframed_values.append(
            value) if value not in self.keyframed_values else ""
        self.app.main_window.keyframe_widget.updateRows()

    def delete_keyframed_value(self, value: DynamicValue):
        self.keyframed_values.remove(
            value) if value in self.keyframed_values else ""
        self.app.main_window.keyframe_widget.updateRows()
