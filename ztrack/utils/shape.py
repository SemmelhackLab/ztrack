from abc import ABC


class Shape(ABC):
    pass


class Ellipse(Shape):
    def __init__(self, cx, cy, a, b, theta):
        self._cx = cx
        self._cy = cy
        self._a = a
        self._b = b
        self._theta = theta


class Circle(Ellipse):
    def __init__(self, cx, cy, r):
        super().__init__(cx, cy, r, r, 0)


class Line(Shape):
    def __init__(self, x0, y0, x1, y1):
        self._x0 = x0
        self._y0 = y0
        self._x1 = x1
        self._y1 = y1


class Rectangle(Shape):
    def __init__(self, x0, y0, w, h):
        self._x0 = x0
        self._y0 = y0
        self._w = w
        self._h = h
