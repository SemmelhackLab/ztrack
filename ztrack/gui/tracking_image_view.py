from abc import abstractmethod
from typing import Dict, List, Optional

import pyqtgraph as pg
from PyQt5 import QtCore, QtWidgets

from ztrack.tracking.tracker import Tracker
from ztrack.tracking.variable import BBox
from ztrack.utils.shape import Ellipse, Shape


class TrackingPlotWidget(pg.PlotWidget):
    roiChanged = QtCore.pyqtSignal(str)

    def __init__(self, parent: QtWidgets.QWidget = None):
        super().__init__(parent)
        pg.setConfigOptions(imageAxisOrder="row-major")
        self._imageItem = pg.ImageItem()
        self._rois: Dict[str, pg.RectROI] = {}
        self._roiGroups: Dict[str, List[ROIGroup]] = {}
        self._currentROIGroups: Dict[str, ROIGroup] = {}
        self._currentTab: Optional[str] = None
        self.addItem(self._imageItem)
        self.invertY(True)
        self.setAspectLocked(1)
        self.hideAxis("bottom")
        self.hideAxis("left")
        self.setBackground(None)

    def setTracker(self, name, index):
        for roi in self._currentROIGroups[name].rois:
            self.removeItem(roi)
        self._currentROIGroups[name] = self._roiGroups[name][index]
        for roi in self._currentROIGroups[name].rois:
            self.addItem(roi)
            roi.setBBox(self._rois[name].bbox)
            for handle in roi.getHandles():
                roi.removeHandle(handle)

    def addTrackerGroup(self, name, trackers: List[Tracker]):
        roi = self.addROI(name)
        self._roiGroups[name] = [ROIGroup.fromTracker(i) for i in trackers]
        for tracker in trackers:
            tracker.bbox = roi.bbox
        roi.sigRegionChanged.connect(lambda: self.roiChanged.emit(name))
        self._currentROIGroups[name] = self._roiGroups[name][0]
        self.setTracker(name, 0)

    def setTrackerGroup(self, name: str):
        self.setROI(name)

    def setRoiVisible(self, b):
        for roi in self._rois.values():
            roi.setVisible(b)

    def setRoiMaxBounds(self, rect):
        for roi in self._rois.values():
            roi.maxBounds = rect

    def setRoiDefaultSize(self, w, h):
        for roi in self._rois.values():
            roi.setDefaultSize(w, h)

    def addROI(self, name):
        roi = RoiBBox(
            None, rotatable=False, movable=False, resizable=False
        )
        roi.setVisible(False)
        self.addItem(roi)
        self._rois[name] = roi
        return roi

    def _disableROI(self, name):
        roi = self._rois[name]
        roi.translatable = False
        roi.resizable = False

    def _enableROI(self, name):
        roi = self._rois[name]
        roi.translatable = True
        roi.resizable = True

    def setROI(self, name):
        if self._currentTab is not None:
            self._disableROI(self._currentTab)
        self._enableROI(name)
        self._currentTab = name

    def setImage(self, img):
        self._imageItem.setImage(img)

    def updateROIGroups(self):
        for roiGroup in self._currentROIGroups.values():
            roiGroup.update()


class RoiBBox(pg.RectROI):
    def __init__(self, bbox=None, **kwargs):
        self._bbox = BBox("", bbox)
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


class ROIGroup:
    def __init__(self, rois):
        self._rois = rois

    @property
    def rois(self):
        return self._rois

    @staticmethod
    def fromTracker(tracker: Tracker):
        return ROIGroup([roiFromShape(shape) for shape in tracker.shapes])

    def update(self):
        for roi in self._rois:
            roi.updateAttr()


def roiFromShape(shape: Shape):
    if isinstance(shape, Ellipse):
        return EllipseROI(shape)


class ShapeMixin:
    @abstractmethod
    def updateAttr(self):
        pass


class EllipseROI(pg.EllipseROI, ShapeMixin):
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
        self.updateAttr()

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

    def updateAttr(self):
        if self._ellipse.visible:
            self.setVisible(True)
            self.setTransformOriginPoint(self.a, self.b)
            self.setPos((self.cx - self.a, self.cy - self.b))
            self.setSize((self.a * 2, self.b * 2))
            self.setRotation(self.theta)
        else:
            self.setVisible(False)
