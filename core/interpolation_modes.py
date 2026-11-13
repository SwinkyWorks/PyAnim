from typing import Any, Self, TYPE_CHECKING
from core.base_plugin import BasePlugin, PluginData
from core.vectors import VectorBase
import math

if TYPE_CHECKING:
    from app import App


class BaseInterpolation:
    name: str = "Base Interpolation"
    available_types: list[type] = [object]

    def __init__(self):
        """Define properties of the interpolation."""
        self.properties: dict[str, tuple[str, float]] = {}

    def interpolate(self, a, b, delta: float, max: float) -> object:
        """Define the funcitonality of your interpolation.\n
        @a: The previous value.\n
        @b: The next value.\n
        @delta: The time since the last keyframe.\n
        @max: The time between keyframes."""
        ...

    def duplicate(self) -> Self:
        d = type(self)()
        d.properties = dict([(k, (v[0], v[1]))
                            for k, v in self.properties.items()])
        return d


class StaticInterpolation(BaseInterpolation):
    """Use the value of the previous keyframe."""

    name: str = "Static"
    available_types: list[type] = [object]

    def interpolate(self, a, b, delta, max):
        return a


class LinearInterpolation(BaseInterpolation):
    """Change at a constant rate."""

    name: str = "Linear"
    available_types: list[type] = [float, VectorBase]

    def interpolate(self, a: Any, b: Any, delta: float, max: float) -> object:
        return a + (b - a) * (delta/max)


class EaseInExponentialInterpolation(BaseInterpolation):
    """Ease in. Customizable."""

    name: str = "Ease In (Exponential)"
    available_types: list[type] = [float, VectorBase]

    def __init__(self):
        self.properties: dict[str, tuple[str, float]] = {
            "degree": ("Interpolation Degree", 1)
        }
    # $x^{e^{d}}$

    def interpolate(self, a: Any, b: Any, delta: float, max: float) -> object:
        x = delta/max
        d = self.properties["degree"][1]
        return a + (b - a) * (x**math.exp(d))


class EaseOutExponentialInterpolation(BaseInterpolation):
    """Ease out. Customizable."""

    name: str = "Ease Out (Exponential)"
    available_types: list[type] = [float, VectorBase]

    def __init__(self):
        self.properties: dict[str, tuple[str, float]] = {
            "degree": ("Interpolation Degree", 1)
        }
    # $1-\left(1-x\right)^{e^{d}}$

    def interpolate(self, a: Any, b: Any, delta: float, max: float) -> object:
        x = delta/max
        d = self.properties["degree"][1]
        return a + (b - a) * (1 - (1 - x)**math.exp(d))


class EaseInOutExponentialInterpolation(BaseInterpolation):
    """Ease in and out. Customizable."""

    name: str = "Ease In/Out (Exponential)"
    available_types: list[type] = [float, VectorBase]

    def __init__(self):
        self.properties: dict[str, tuple[str, float]] = {
            "degree": ("Interpolation Degree", 1)
        }
    # $\left\{x<0.5:\frac{x^{e^{d}}}{2\left(0.5\right)^{e^{d}}},1-\frac{\left(1-x\right)^{e^{d}}}{2\left(0.5\right)^{e^{d}}}\right\}$

    def interpolate(self, a: Any, b: Any, delta: float, max: float) -> object:
        x = delta/max
        d = self.properties["degree"][1]
        if (x < 0.5):
            return a + (b - a) * (x**math.exp(d)) / 2 / 0.5 ** math.exp(d)
        else:
            return a + (b - a) * (1 - ((1 - x)**math.exp(d)) / 2 / 0.5 ** math.exp(d))


class EaseInQuadraticInterpolation(BaseInterpolation):
    """Ease in. Perfect for constant acceleration."""

    name: str = "Ease In (Quadratic)"
    available_types: list[type] = [float, VectorBase]

    def interpolate(self, a: Any, b: Any, delta: float, max: float) -> object:
        x = delta/max
        return b + (1 - x*x) * (a - b)


class EaseOutQuadraticInterpolation(BaseInterpolation):
    """Ease out. Perfect for constant acceleration."""

    name: str = "Ease Out (Quadratic)"
    available_types: list[type] = [float, VectorBase]

    def interpolate(self, a: Any, b: Any, delta: float, max: float) -> object:
        x = delta/max
        return b + (x - 1)*(x - 1) * (a - b)


class EaseInOutQuadraticInterpolation(BaseInterpolation):
    """Ease in and out. Perfect for constant (except a flip in the middle) acceleration."""

    name: str = "Ease Out (Quadratic)"
    available_types: list[type] = [float, VectorBase]

    def interpolate(self, a: Any, b: Any, delta: float, max: float) -> Any:
        x = delta/max

        if (x < 0.5):
            return b + (1 - x*x) * (a - b)
        else:
            return b + (x - 1)*(x - 1) * (a - b)


class SinInterpolation(BaseInterpolation):
    """Sin. Wave borders are manual."""

    name: str = "Sin"
    available_types: list[type] = [float]

    def __init__(self):
        self.properties: dict[str, tuple[str, float]] = {
            "min": ("Min value", 0),
            "max": ("Max value", 1),
            "span": ("Span (Degrees)", 180),
            "offset": ("Offset (Degrees)", 0)
        }

    def interpolate(self, a: object, b: object, delta: float, max: float) -> object:
        ax = self.properties["min"][1]
        bx = self.properties["max"][1]
        s = self.properties["span"][1]
        o = self.properties["offset"][1]
        x = delta / max

        return ax + (bx - ax) * (math.sin(math.radians(s * x + o)) + 1) / 2


def register_interpolation_modes(app: "App"):
    p = BasePlugin(app, PluginData())
    app.timeline_manager.register_interpolation_mode(p, StaticInterpolation)  # nopep8
    app.timeline_manager.register_interpolation_mode(p, LinearInterpolation)  # nopep8
    app.timeline_manager.register_interpolation_mode(p, EaseInExponentialInterpolation)  # nopep8
    app.timeline_manager.register_interpolation_mode(p, EaseOutExponentialInterpolation)  # nopep8
    app.timeline_manager.register_interpolation_mode(p, EaseInOutExponentialInterpolation)  # nopep8
    app.timeline_manager.register_interpolation_mode(p, EaseInQuadraticInterpolation)  # nopep8
    app.timeline_manager.register_interpolation_mode(p, EaseOutQuadraticInterpolation)  # nopep8
    app.timeline_manager.register_interpolation_mode(p, EaseInOutQuadraticInterpolation)  # nopep8
    app.timeline_manager.register_interpolation_mode(p, SinInterpolation)  # nopep8
