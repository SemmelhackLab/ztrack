from abc import ABC

from ztrack.utils.variable import Rect


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


class Ellipse(Shape):
    def __init__(
        self, cx: float, cy: float, a: float, b: float, theta: float, lw, lc
    ):
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
