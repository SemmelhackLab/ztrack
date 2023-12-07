from __future__ import annotations

from abc import ABC
from typing import TYPE_CHECKING

import numpy as np

from ztrack.utils.variable import Rect

if TYPE_CHECKING:
    from ztrack.utils.typing import point2d


class Shape(ABC):
    def __init__(self, lw, lc):
        self.lw = lw
        self.lc = lc
        self._bbox = Rect("")
        self._visible = True

    @property
    def visible(self):
        return self._visible

    @visible.setter
    def visible(self, visible: bool):
        self._visible = visible

    def set_bbox(self, bbox):
        self._bbox = bbox

    @property
    def origin(self) -> point2d:
        return 0, 0 if self._bbox.value is None else self._bbox.value[:2]


class Points(Shape):
    def __init__(self, data: np.ndarray, lw, lc, symbol):
        super().__init__(lw, lc)
        self._data = data
        self.symbol = symbol

    @property
    def data(self):
        if self._bbox.value is None:
            return self._data
        return self._data + self._bbox.value[:2]

    @data.setter
    def data(self, data):
        self._data = data


class Rectangle(Shape):
    def __init__(self, x: float, y: float, w: float, h: float, lw, lc):
        super().__init__(lw, lc)
        self._x = x
        self._y = y
        self.w = w
        self.h = h

    @property
    def x(self):
        if self._bbox.value is None:
            return self._x
        return self._x + self._bbox.value[0]

    @x.setter
    def x(self, x: float):
        self._x = x

    @property
    def y(self):
        if self._bbox.value is None:
            return self._y
        return self._y + self._bbox.value[1]

    @y.setter
    def y(self, y: float):
        self._y = y


class Ellipse(Shape):
    def __init__(self, cx: float, cy: float, a: float, b: float, theta: float, lw, lc):
        super().__init__(lw, lc)
        self._cx = cx
        self._cy = cy
        self.a = a
        self.b = b
        self.theta = theta

    @property
    def cx(self):
        if self._bbox.value is None:
            return self._cx
        return self._cx + self._bbox.value[0]

    @cx.setter
    def cx(self, cx: float):
        self._cx = cx

    @property
    def cy(self):
        if self._bbox.value is None:
            return self._cy
        return self._cy + self._bbox.value[1]

    @cy.setter
    def cy(self, cy: float):
        self._cy = cy


class Circle(Ellipse):
    def __init__(self, cx: float, cy: float, r: float, lw, lc):
        super().__init__(cx, cy, r, r, 0, lw, lc)

    @property
    def r(self):
        return self.a

    @r.setter
    def r(self, r: float):
        self.a = r
        self.b = r


class Line(Shape):
    def __init__(self, x1: float, x2: float, y1: float, y2: float, lw, lc):
        super().__init__(lw, lc)
        self._x1 = x1
        self._x2 = x2
        self._y1 = y1
        self._y2 = y2

    @property
    def x1(self):
        if self._bbox.value is None:
            return self._x1
        return self._x1 + self._bbox.value[0]

    @x1.setter
    def x1(self, x1: float):
        self._x1 = x1

    @property
    def x2(self):
        if self._bbox.value is None:
            return self._x2
        return self._x2 + self._bbox.value[0]

    @x2.setter
    def x2(self, x2: float):
        self._x2 = x2

    @property
    def y1(self):
        if self._bbox.value is None:
            return self._y1
        return self._y1 + self._bbox.value[1]

    @y1.setter
    def y1(self, y1: float):
        self._y1 = y1

    @property
    def y2(self):
        if self._bbox.value is None:
            return self._y2
        return self._y2 + self._bbox.value[1]

    @y2.setter
    def y2(self, y2: float):
        self._y2 = y2

    def set_center_length_angle(self, center, length, angle):
        center = np.asarray(center)
        v = (length / 2) * np.array((np.cos(angle), np.sin(angle)))
        (self.x1, self.y1), (self.x2, self.y2) = center - v, center + v
