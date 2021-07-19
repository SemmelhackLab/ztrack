from abc import abstractmethod
from typing import Dict, List, Iterable, Optional

import pyqtgraph as pg
from PyQt5 import QtCore, QtWidgets

from ztrack.tracking.tracker import Tracker
from ztrack.utils.variable import Rect
from ztrack.utils.shape import Ellipse, Shape

pg.setConfigOptions(imageAxisOrder="row-major")


class TrackingPlotWidget(pg.PlotWidget):
    roiChanged = QtCore.pyqtSignal(str)

    def __init__(self, parent: QtWidgets.QWidget = None):
        super().__init__(parent)
        self._imageItem = pg.ImageItem()
        self._rois: Dict[str, pg.RectROI] = {}
        self._shapeGroups: Dict[str, List[ShapeGroup]] = {}
        self._currentShapeGroup: Dict[str, ShapeGroup] = {}
        self._currentTab: Optional[str] = None

        self.addItem(self._imageItem)
        self.invertY(True)
        self.setAspectLocked(1)
        self.hideAxis("left")
        self.hideAxis("bottom")
        self.setBackground(None)

    def setTracker(self, group_name: str, index: int):
        for roi in self._currentShapeGroup[group_name].shapes:
            self.removeItem(roi)
        self._currentShapeGroup[group_name] = self._shapeGroups[group_name][index]
        for roi in self._currentShapeGroup[group_name].shapes:
            self.addItem(roi)
            roi.setBBox(self._rois[group_name].bbox)
            for handle in roi.getHandles():
                roi.removeHandle(handle)

    def addTrackerGroup(self, group_name: str, trackers: Iterable[Tracker]):
        roi = self.addRoi(group_name)
        self._shapeGroups[group_name] = [ShapeGroup.fromTracker(i) for i in trackers]
        for tracker in trackers:
            tracker.bbox = roi.bbox
        roi.sigRegionChanged.connect(lambda: self.roiChanged.emit(group_name))
        self._currentShapeGroup[group_name] = self._shapeGroups[group_name][0]
        self.setTracker(group_name, 0)

    def setTrackerGroup(self, name: str):
        self._setCurrentRoi(name)

    def setRoiMaxBounds(self, rect):
        for roi in self._rois.values():
            roi.maxBounds = rect

    def setRoiDefaultSize(self, w, h):
        for roi in self._rois.values():
            roi.setDefaultSize(w, h)

    def addRoi(self, name):
        roi = Roi(None, rotatable=False)
        self.addItem(roi)
        roi.setVisible(False)
        self._rois[name] = roi
        return roi

    def _setCurrentRoi(self, name):
        if self._currentTab is not None:
            self._rois[self._currentTab].setVisible(False)
        self._rois[name].setVisible(True)
        self._currentTab = name

    def setImage(self, img):
        self._imageItem.setImage(img)

    def updateRoiGroups(self):
        for roiGroup in self._currentShapeGroup.values():
            roiGroup.update()


class Roi(pg.RectROI):
    def __init__(self, bbox=None, **kwargs):
        self._bbox = Rect("", bbox)
        self._default_origin = 0, 0
        self._default_size = 100, 100

        super().__init__(self._pos, self._size, **kwargs)
        self.sigRegionChanged.connect(self._onRegionChanged)

    @property
    def _pos(self):
        if self._bbox.value is None:
            return self._default_origin
        return self._bbox.value[:2]

    @property
    def _size(self):
        if self._bbox.value is None:
            return self._default_size
        return self._bbox.value[2:]

    def setDefaultSize(self, w, h):
        self._default_size = w, h
        self.setSize(self._size)

    @property
    def bbox(self):
        return self._bbox

    def _onRegionChanged(self):
        x, y = self.pos()
        w, h = self.size()
        self._bbox.value = (x, y, w, h)


class ShapeGroup:
    def __init__(self, shapes: List[pg.ROI]):
        self._shapes = shapes

    @property
    def shapes(self):
        return self._shapes

    @staticmethod
    def fromTracker(tracker: Tracker):
        return ShapeGroup([roiFromShape(shape) for shape in tracker.shapes])

    def update(self):
        for roi in self._shapes:
            roi.refresh()


def roiFromShape(shape: Shape):
    if isinstance(shape, Ellipse):
        return EllipseRoi(shape)


class ShapeMixin:
    @abstractmethod
    def refresh(self):
        pass


class EllipseRoi(pg.EllipseROI, ShapeMixin):
    def __init__(self, ellipse: Ellipse):
        self._ellipse = ellipse
        super().__init__(
            pos=(0, 0),
            size=(1, 1),
            pen=pg.mkPen(ellipse.lc, width=ellipse.lw),
            movable=False,
            resizable=False,
            rotatable=False,
        )
        self.refresh()

    def setBBox(self, bbox):
        self._ellipse.set_bbox(bbox)

    @property
    def cx(self):
        return self._ellipse.cx

    @property
    def cy(self):
        return self._ellipse.cy

    @property
    def a(self):
        return self._ellipse.a

    @property
    def b(self):
        return self._ellipse.b

    @property
    def theta(self):
        return self._ellipse.theta

    def refresh(self):
        if self._ellipse.visible:
            self.setVisible(True)
            self.setTransformOriginPoint(self.a, self.b)
            self.setPos((self.cx - self.a, self.cy - self.b))
            self.setSize((self.a * 2, self.b * 2))
            self.setRotation(self.theta)
        else:
            self.setVisible(False)
