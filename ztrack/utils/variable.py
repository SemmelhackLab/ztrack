from abc import ABC, abstractmethod
from typing import Optional, Tuple

import numpy as np

_rect = Optional[Tuple[int, int, int, int]]
_point = Tuple[int, int]


class Variable(ABC):
    def __init__(self, display_name: str):
        self._display_name = display_name

    @property
    def display_name(self):
        return self._display_name

    @property
    @abstractmethod
    def value(self):
        pass

    @value.setter
    def value(self, value):
        pass


class Angle(Variable):
    def __init__(self, display_name: str, angle: float):
        super().__init__(display_name)
        self._value = 0
        self.value = angle

    @property
    def value(self) -> float:
        return self._value

    @value.setter
    def value(self, value: float):
        self._value = int(value) % 360


class Point(Variable):
    def __init__(self, display_name: str, point):
        super().__init__(display_name)

        x, y = point
        point = x, y
        self._value = point

    @property
    def value(self) -> _point:
        return self._value

    @value.setter
    def value(self, value: _point):
        self._value = value


class String(Variable):
    def __init__(self, display_name: str, string):
        super().__init__(display_name)
        self._value = string

    @property
    def value(self) -> str:
        return self._value

    @value.setter
    def value(self, value: str):
        self._value = value


class Rect(Variable):
    def __init__(self, display_name: str, bbox=None):
        super().__init__(display_name)
        if bbox is not None:
            x, y, w, h = bbox
            bbox = x, y, w, h
        self._value = bbox

    @property
    def value(self) -> _rect:
        return self._value

    @value.setter
    def value(self, value: _rect):
        self._value = self._normalize(value)

    @staticmethod
    def _normalize(roi: _rect = None):
        if roi is not None:

            def relu(a):
                return max(0, a)

            x, y, width, height = map(int, roi)
            x0, x1 = sorted(map(relu, (x, x + width)))
            y0, y1 = sorted(map(relu, (y, y + height)))
            return x0, y0, x1 - x0, y1 - y0

    def to_slice(self, axis=0):
        if self._value is None:
            return np.s_[:]
        x, y, width, height = self._value
        return (np.s_[:],) * axis + np.s_[y : y + height, x : x + width]


class Numerical(Variable, ABC):
    def __init__(self, display_name: str, value):
        super().__init__(display_name)
        self._value = value

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, value):
        self._value = value


class Bounded(Numerical, ABC):
    def __init__(self, display_name: str, value, minimum, maximum):
        super().__init__(display_name, value)
        assert minimum <= value <= maximum
        self._minimum = minimum
        self._maximum = maximum

    @property
    def value(self):
        return super().value

    @value.setter
    def value(self, value):
        assert self._minimum <= value <= self._maximum
        self._value = value

    @property
    def minimum(self):
        return self._minimum

    @property
    def maximum(self):
        return self._maximum


class Int(Bounded):
    def __init__(
        self,
        display_name: str,
        value: int,
        minimum: int,
        maximum: int,
        odd_only=False,
    ):
        super().__init__(display_name, value, minimum, maximum)
        self._odd_only = odd_only

    @property
    def value(self):
        return super().value

    @value.setter
    def value(self, value):
        assert self._minimum <= value <= self._maximum

        if self._odd_only and value % 2 == 0:
            value += 1

        self._value = value


class UInt8(Int):
    def __init__(self, display_name: str, value: int):
        super().__init__(display_name, value, 0, 255)


class Float(Bounded):
    def __init__(
        self,
        display_name: str,
        value: float,
        minimum: float,
        maximum: float,
        step: float,
    ):
        super().__init__(display_name, value, minimum, maximum)
        self._step = step

    @property
    def step(self):
        return self._step
