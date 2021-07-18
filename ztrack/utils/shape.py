from abc import ABC

from ztrack.tracking.variable import BBox


class Shape(ABC):
    def __init__(self, lw, lc):
        self.lw = lw
        self.lc = lc
        self._bbox = BBox("")
        self._visible = True

    @property
    def visible(self):
        return self._visible

    @visible.setter
    def visible(self, visible: bool):
        self._visible = visible

    def set_bbox(self, bbox):
        self._bbox = bbox


class Ellipse(Shape):
    def __init__(self, cx, cy, a, b, theta, lw, lc):
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
    def cx(self, cx):
        self._cx = cx

    @property
    def cy(self):
        if self._bbox.value is None:
            return self._cy
        return self._cy + self._bbox.value[1]

    @cy.setter
    def cy(self, cy):
        self._cy = cy


# class Circle(Ellipse):
#     def __init__(self, cx, cy, r, lw, lc):
#         super().__init__(cx, cy, r, r, 0, lw, lc)
#
#
# class Line(Shape):
#     def __init__(self, x0, y0, x1, y1, lw, lc):
#         super().__init__(lw, lc)
#         self.x0 = x0
#         self.y0 = y0
#         self.x1 = x1
#         self.y1 = y1
#
#
# class Rectangle(Shape):
#     def __init__(self, x0, y0, w, h, lw, lc):
#         super().__init__(lw, lc)
#         self.x0 = x0
#         self.y0 = y0
#         self.w = w
#         self.h = h
