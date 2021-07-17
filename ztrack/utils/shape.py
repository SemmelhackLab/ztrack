from abc import ABC


class Shape(ABC):
    pass


class Ellipse(Shape):
    def __init__(self, cx, cy, a, b, theta):
        self.cx = cx
        self.cy = cy
        self.a = a
        self.b = b
        self.theta = theta


class Circle(Ellipse):
    def __init__(self, cx, cy, r):
        super().__init__(cx, cy, r, r, 0)


class Line(Shape):
    def __init__(self, x0, y0, x1, y1):
        self.x0 = x0
        self.y0 = y0
        self.x1 = x1
        self.y1 = y1


class Rectangle(Shape):
    def __init__(self, x0, y0, w, h):
        self.x0 = x0
        self.y0 = y0
        self.w = w
        self.h = h
