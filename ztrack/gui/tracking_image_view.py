from abc import abstractmethod
from typing import Dict, List, Optional

import pyqtgraph as pg
from PyQt5 import QtWidgets

from ztrack.tracking.tracker import Tracker
from ztrack.utils.shape import Ellipse, Shape


class TrackingPlotWidget(pg.PlotWidget):
    def __init__(self, parent: QtWidgets.QWidget = None):
        super().__init__(parent)
        pg.setConfigOptions(imageAxisOrder="row-major")
        self._imageItem = pg.ImageItem()
        self._rois: List[pg.RectROI] = []
        self._roiGroups: Dict[str, List[ROIGroup]] = {}
        self._currentROIGroups: Dict[str, ROIGroup] = {}
        self._currentROI: Optional[int] = None
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
            for handle in roi.getHandles():
                roi.removeHandle(handle)

    def addTrackerGroup(self, name, trackers: List[Tracker]):
        self.addROI()
        self._roiGroups[name] = [ROIGroup.fromTracker(i) for i in trackers]
        self._currentROIGroups[name] = self._roiGroups[name][0]
        self.setTracker(name, 0)

    def setTrackerGroup(self, index: int):
        self.setROI(index)

    def addROI(self):
        roi = pg.RectROI(
            (0, 0), (100, 100), rotatable=False, movable=False, resizable=False
        )
        self.addItem(roi)
        self._rois.append(roi)

    def _disableROI(self, index):
        roi = self._rois[index]
        roi.translatable = False
        roi.resizable = False

    def _enableROI(self, index):
        roi = self._rois[index]
        roi.translatable = True
        roi.resizable = True

    def setROI(self, index: int):
        if self._currentROI is not None:
            self._disableROI(self._currentROI)
        self._enableROI(index)
        self._currentROI = index

    def setImage(self, img):
        self._imageItem.setImage(img)

    def updateROIGroups(self):
        for roiGroup in self._currentROIGroups.values():
            roiGroup.update()


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
        self.setTransformOriginPoint(self.a, self.b)
        self.setPos((self.cx - self.a, self.cy - self.b))
        self.setSize((self.a * 2, self.b * 2))
        self.setRotation(self.theta)
