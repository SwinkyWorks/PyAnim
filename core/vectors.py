from typing import Union, TypeVar, Protocol, Self, overload
from PySide6.QtCore import QPoint, QPointF, QSize, QSizeF
import math


TVector = TypeVar("TVector", bound="VectorBase")


class VectorBase:
    """A base class for vectors."""

    def __init__(self, *values: float) -> None:
        """A base class for vectors."""
        self._values = list(values)[:self.numAxes] + \
            [0.0]*(self.numAxes - len(self._values))
        self._curr = 0

    numAxes: int = 1
    axisMapping: list[str] = ["v"]

    def __add__(self, other: "VectorBase") -> Self:
        return type(self)(*[a + b for a, b in zip(self._values, other._values)])

    def __sub__(self, other: "VectorBase") -> Self:
        return type(self)(*[a - b for a, b in zip(self._values, other._values)])

    def __mul__(self, other: Union["VectorBase", float]) -> Self:
        if isinstance(other, VectorBase):
            return type(self)(*[a * b for a, b in zip(self._values, other._values)])
        else:
            return type(self)(*[a * other for a in self._values])

    def __truediv__(self, other: Union["VectorBase", float]) -> Self:
        if isinstance(other, VectorBase):
            return type(self)(*[a / b for a, b in zip(self._values, other._values)])
        else:
            return type(self)(*[a / other for a in self._values])

    def __floordiv__(self, other: Union["VectorBase", float]) -> Self:
        if isinstance(other, VectorBase):
            return type(self)(*[a // b for a, b in zip(self._values, other._values)])
        else:
            return type(self)(*[a // other for a in self._values])

    def __rmul__(self, other: Union["VectorBase", float]) -> Self:
        return self * other

    def __rtruediv__(self, other: Union["VectorBase", float]) -> Self:
        if isinstance(other, VectorBase):
            return type(self)(*[b / a for a, b in zip(self._values, other._values)])
        else:
            return type(self)(*[other / a for a in self._values])

    def __rfloordiv__(self, other: Union["VectorBase", float]) -> Self:
        if isinstance(other, VectorBase):
            return type(self)(*[b // a for a, b in zip(self._values, other._values)])
        else:
            return type(self)(*[other // a for a in self._values])

    def __eq__(self, other: object) -> bool:
        if isinstance(other, VectorBase):
            if (self.numAxes <= other.numAxes):
                return all(a == b for a, b in zip(self._values, other._values))
        return False

    def __neg__(self) -> Self:
        return type(self)(*[-a for a in self._values])

    @property
    def length(self) -> float:
        return math.sqrt(sum(a*a for a in self._values))

    @property
    def normalized(self) -> Self:
        return self / self.length

    def dot(self, other: 'VectorBase') -> float:
        # could also be written as `sum((self*other)._values)`
        return sum(a*b for a, b in zip(self._values, other._values))

    def lerp(self, other: 'VectorBase', t: float) -> Self:
        # Dead simple. Also, with a `t` of `1/2`, directly equates to `(self + other) / 2`.
        return self + (other - self) * t

    # $a + \frac{b - a}{2}$
    # $a + \frac{b}{2} - \frac{a}{2}$
    # $a - \frac{a}{2} + \frac{b}{2}$
    # $\frac{a}{2} + \frac{b}{2}$
    # $\frac{a + b}{2}$

    def distance_to(self, other: Union['VectorBase', None]) -> float:
        return (other - self).length if other != None else 0.0

    def __repr__(
        self) -> str: return f"VectorBase({", ".join([str(a) for a in self._values])})"

    @staticmethod
    def bound(boundsMin: 'VectorBase', boundsMax: 'VectorBase', value: 'VectorBase') -> 'VectorBase':
        t = type(
            value
            if (
                (boundsMax == None or value.numAxes <= boundsMax.numAxes)
                and (boundsMin == None or value.numAxes <= boundsMin.numAxes)
            )
            else boundsMax
            if (boundsMin == None or boundsMax.numAxes <= boundsMin.numAxes)
            else boundsMin)

        if boundsMax != None and boundsMin != None:
            return t(*[max(a, min(c, b)) for a, b, c in zip(boundsMin._values, boundsMax._values, value._values)])
        elif boundsMax != None:
            return t(*[min(c, b) for b, c in zip(boundsMax._values, value._values)])
        elif boundsMin != None:
            return t(*[max(c, a) for a, c in zip(boundsMin._values, value._values)])
        else:
            return t(*[c for c in value._values])

    def __iter__(self) -> Self:
        self._curr = 0
        return self

    def __next__(self) -> float:
        if self._curr < self.numAxes:
            self._curr += 1
            return self._values[self._curr - 1]
        else:
            raise StopIteration()

    @overload
    def __getitem__(self, indicies: int | str) -> float:
        ...

    @overload
    def __getitem__(self, indicies: tuple[int | str]) -> tuple[float]:
        ...

    def __getitem__(self, indicies: int | str | tuple[int | str]) -> float | tuple[float]:
        if not isinstance(indicies, tuple):
            i = 0
            if (isinstance(indicies, int)):
                i = indicies
            elif isinstance(indicies, str):
                i = self.axisMapping.index(
                    indicies) if indicies in self.axisMapping else -1

            if i >= 0 and i < self.numAxes:
                return self._values[i]
            else:
                try:
                    raise IndexError(f"Index \"{indicies}\" not in vector",)
                except IndexError as e:
                    e.with_traceback(None)
                    raise

        returns = []
        for index in indicies:
            i = 0
            if (isinstance(index, int)):
                i = index
            elif isinstance(index, str):
                i = self.axisMapping.index(
                    index) if index in self.axisMapping else -1

            if i >= 0 and i < self.numAxes:
                returns.append(self._values[i])
            else:
                try:
                    raise IndexError(f"Index \"{indicies}\" not in vector",)
                except IndexError as e:
                    e.with_traceback(None)
                    raise

        return tuple(returns)

    def __setitem__(self, indicies, values) -> None:
        if not isinstance(indicies, tuple):
            i = 0
            if (isinstance(indicies, int)):
                i = indicies
            elif isinstance(indicies, str):
                i = self.axisMapping.index(
                    indicies) if indicies in self.axisMapping else -1

            if i >= 0 and i < self.numAxes:
                self._values[i] = values
            else:
                try:
                    raise IndexError(f"Index \"{indicies}\" not in vector")
                except IndexError as e:
                    e.with_traceback(None)
                    raise
        else:
            for index, value in zip(indicies, values):
                i = 0
                if (isinstance(index, int)):
                    i = index
                elif isinstance(index, str):
                    i = self.axisMapping.index(
                        index) if index in self.axisMapping else -1

                if i >= 0 and i < self.numAxes:
                    self._values[i] = value
                else:
                    try:
                        raise IndexError(
                            f"Index \"{indicies}\" not in vector",)
                    except IndexError as e:
                        e.with_traceback(None)
                        raise

    def rounddiv(self, other: Union["VectorBase", float]) -> Self:
        if isinstance(other, VectorBase):
            return type(self)(*[round(a / b) for a, b in zip(self._values, other._values)])
        else:
            return type(self)(*[round(a / other) for a in self._values])

    def rrounddiv(self, other: Union["VectorBase", float]) -> Self:
        if isinstance(other, VectorBase):
            return type(self)(*[round(a / b) for a, b in zip(self._values, other._values)])
        else:
            return type(self)(*[round(a / other) for a in self._values])

    def floor(self) -> Self:
        return type(self)(*[math.floor(a) for a in self._values])

    def __floor__(self) -> Self: return self.floor()

    def ceil(self) -> Self:
        return type(self)(*[math.ceil(a) for a in self._values])

    def __ceil__(self) -> Self: return self.ceil()

    def __abs__(self) -> Self:
        return type(self)(*[abs(a) for a in self._values])

    def __min__(self, other) -> Self:
        return type(self)(*[min(a, b) for a, b in zip(self._values, other._values)])

    def __max__(self, other) -> Self:
        return type(self)(*[max(a, b) for a, b in zip(self._values, other._values)])

    @staticmethod
    def min(a: TVector, b: "VectorBase") -> TVector:
        return a.__min__(b)

    @staticmethod
    def max(a: TVector, b: "VectorBase") -> TVector:
        return a.__max__(b)

    def clone(self) -> Self:
        return type(self)(*self._values)


class Vec2(VectorBase):
    """
    A Vector2 implementation that includes many animation-essential functions, such as lerp, dot, and rotate, as well as some PySide6 inter-operation functions.
    """

    def __init__(self, x: Union[float, 'Vec2', 'Vec3', QPoint, QSize, None] = None, y: float | None = None, *_) -> None:
        """
        A Vector2 implementation that includes many animation-essential functions, such as lerp, dot, and rotate, as well as some PySide6 inter-operation functions. \n
        () -> (0,0) \n
        (a) -> (a,a) \n
        (a,b) -> (a,b) \n
        (v2) -> (v2.x, v2.y) \n
        (v3) -> (v3.x, v3.y)
        """
        self._values = [0.0, 0.0]

        if isinstance(x, (Vec2, Vec3)):
            self._values[0] = x.x
            self._values[1] = x.y
        elif isinstance(x, QPoint):
            self._values[0] = float(x.x())
            self._values[1] = float(x.y())
        elif isinstance(x, QSize):
            self._values[0] = float(x.width())
            self._values[1] = float(x.height())
        else:
            self._values[0] = float(x) if x != None else 0.0
            self._values[1] = float(
                y) if y != None else x if x != None else 0.0

        self._curr = 0

    numAxes = 2
    axisMapping = ["x", "y"]

    @property
    def x(self) -> float:
        return self._values[0]

    @x.setter
    def x(self, value: float) -> None:
        self._values[0] = value

    @property
    def y(self) -> float:
        return self._values[1]

    @y.setter
    def y(self, value: float) -> None:
        self._values[1] = value

    @property
    def angle(self) -> float:
        return math.atan2(self._values[1], self._values[0])

    def rotate(self, angle: float) -> 'Vec2':
        return Vec2(math.cos(angle)*self._values[0] - math.sin(angle)*self._values[1], math.sin(angle)*self._values[0] + math.cos(angle)*self._values[1])

    @property
    def qpoint(self) -> QPoint:
        return QPoint(int(self._values[0]), int(self._values[1]))

    @qpoint.setter
    def qpoint(self, value: QPoint) -> None:  # vec2.qpoint = QPoint(1,2)
        self._values[0] = float(value.x())     # vec2 == Vec2(1,2)
        self._values[1] = float(value.y())

    @property
    def qpointf(self) -> QPointF:
        return QPointF(self._values[0], self._values[1])

    @qpointf.setter
    def qpointf(self, value: QPointF) -> None:
        self._values[0] = value.x()
        self._values[1] = value.y()

    @property
    def qsize(self) -> QSize:
        return QSize(int(self._values[0]), int(self._values[1]))

    @qsize.setter
    def qsize(self, value: QSize) -> None:
        self._values[0] = float(value.width())
        self._values[1] = float(value.height())

    @property
    def qsizef(self) -> QSizeF:
        return QSizeF(self._values[0], self._values[1])

    @qsizef.setter
    def qsizef(self, value: QSizeF) -> None:
        self._values[0] = value.width()
        self._values[1] = value.height()

    def __repr__(
        self) -> str: return f"Vec2({", ".join([str(a) for a in self._values])})"


class Vec3(VectorBase):
    """
    A Vector3 implementation that includes many animation-essential functions, such as lerp, dot, and cross.
    """

    def __init__(self, x: Union[float, Vec2, 'Vec3', None] = None, y: float | None = None, z: float | None = None):
        """
        A Vector3 implementation that includes many animation-essential functions, such as lerp, dot, and cross. \n
        () -> (0,0,0) \n
        (a) -> (a,a,a) \n
        (a,b) -> (a,b,0) \n
        (a,b,c) -> (a,b,c) \n
        (v2) -> (v2.x, v2.y, 0) \n
        (v2, z) -> (v2.x, v2.y, z) \n
        (v3) -> (v3.x, v3.y, v3.z)
        """
        self._values = [0.0, 0.0, 0.0]

        if isinstance(x, Vec2):
            self._values[0] = x._values[0]
            self._values[1] = x._values[1]
            self._values[2] = y if y != None else 0.0
        elif isinstance(x, Vec3):
            self._values[0] = x._values[0]
            self._values[1] = x._values[1]
            self._values[2] = x._values[2]
        elif x == None:
            self._values[0] = 0.0
            self._values[1] = 0.0
            self._values[2] = 0.0
        else:
            self._values[0] = float(x)
            if y == None:
                self._values[1] = float(x)
                self._values[2] = float(x)
            else:
                self._values[1] = float(y)
                self._values[2] = float(z) if z != None else 0.0

        self._curr = 0

    numAxes = 3
    axisMapping = ["x", "y", "z"]

    @property
    def x(self):
        return self._values[0]

    @x.setter
    def x(self, value: float):
        self._values[0] = value

    @property
    def y(self):
        return self._values[1]

    @y.setter
    def y(self, value: float):
        self._values[1] = value

    @property
    def z(self):
        return self._values[2]

    @z.setter
    def z(self, value: float):
        self._values[2] = value

    def cross(self, other: 'Vec3'):
        return Vec3(self._values[1] * other._values[2] - self._values[2] * other._values[1], self._values[2] * other._values[0] - self._values[0] * other._values[2], self._values[0] * other._values[1] - self._values[1] * other._values[0])

    def angle(self, plane: str = "xy"):
        if (plane == "xy"):
            return math.atan2(self._values[1], self._values[0])
        if (plane == "yx"):
            return math.atan2(self._values[0], self._values[1])
        if (plane == "xz"):
            return math.atan2(self._values[2], self._values[0])
        if (plane == "zx"):
            return math.atan2(self._values[0], self._values[2])
        if (plane == "yz"):
            return math.atan2(self._values[2], self._values[1])
        if (plane == "zy"):
            return math.atan2(self._values[1], self._values[2])
        return 0.0

    def rotate(self, angle: float, plane: str = "xy"):
        if (plane == "xy"):
            return Vec3(math.cos(angle)*self._values[0] - math.sin(angle)*self._values[1], math.sin(angle)*self._values[0] + math.cos(angle)*self._values[1], self._values[2])
        if (plane == "yx"):
            return Vec3(math.sin(angle)*self._values[1] + math.cos(angle)*self._values[0], math.cos(angle)*self._values[1] - math.sin(angle)*self._values[0], self._values[2])
        if (plane == "xz"):
            return Vec3(math.cos(angle)*self._values[0] - math.sin(angle)*self._values[2], self._values[1], math.sin(angle)*self._values[0] + math.cos(angle)*self._values[2])
        if (plane == "zx"):
            return Vec3(math.sin(angle)*self._values[2] + math.cos(angle)*self._values[0], self._values[1], math.cos(angle)*self._values[2] - math.sin(angle)*self._values[0])
        if (plane == "yz"):
            return Vec3(self._values[0], math.cos(angle)*self._values[1] - math.sin(angle)*self._values[2], math.sin(angle)*self._values[1] + math.cos(angle)*self._values[2])
        if (plane == "zy"):
            return Vec3(self._values[0], math.sin(angle)*self._values[2] + math.cos(angle)*self._values[1], math.cos(angle)*self._values[2] - math.sin(angle)*self._values[1])
        return Vec3(self)

    def __repr__(
        self) -> str: return f"Vec3({", ".join([str(a) for a in self._values])})"
