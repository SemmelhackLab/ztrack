from abc import abstractmethod
from typing import Dict, Iterable, List, Optional

import pyqtgraph as pg
from PyQt5 import QtCore, QtGui, QtWidgets

from ztrack.tracking.tracker import Tracker
from ztrack.utils.shape import Ellipse, Points, Shape
from ztrack.utils.variable import Rect

pg.setConfigOptions(imageAxisOrder="row-major")


class TrackingPlotWidget(pg.PlotWidget):
    roiChanged = QtCore.pyqtSignal(str)
    pointSelected = QtCore.pyqtSignal(int, int)

    def __init__(self, parent: QtWidgets.QWidget = None):
        super().__init__(parent)

        self._imageItem = pg.ImageItem()
        self._rois: Dict[str, Roi] = {}
        self._shapeGroups: Dict[str, List[ShapeGroup]] = {}
        self._currentShapeGroup: Dict[str, ShapeGroup] = {}
        self._currentTab: Optional[str] = None
        self._pointSelectionModeEnabled = False

        self.addItem(self._imageItem)
        self.invertY(True)
        self.setAspectLocked(1)
        self.hideAxis("left")
        self.hideAxis("bottom")
        self.setBackground(None)
        self.scene().sigMouseClicked.connect(self._onMouseClicked)
        self.setRenderHints(QtGui.QPainter.Antialiasing)

    def setPointSelectionModeEnabled(self, enabled):
        self._pointSelectionModeEnabled = enabled
        roi = self._rois[self._currentTab]
        roi.resizable = roi.translatable = not enabled
        self.setCursor(
            QtCore.Qt.CrossCursor if enabled else QtCore.Qt.ArrowCursor
        )

    def _onMouseClicked(self, event):
        if self._pointSelectionModeEnabled:
            pos = event.currentItem.mapSceneToView(event.scenePos())
            self.pointSelected.emit(int(pos.x()), int(pos.y()))

    def setStateFromTrackingConfig(self, trackingConfig: dict):
        for groupName, groupDict in trackingConfig.items():
            self._rois[groupName].setRect(groupDict["roi"])

    def setEnabled(self, b: bool):
        for shapeGroup in self._currentShapeGroup.values():
            for shape in shapeGroup.shapes:
                shape.setVisible(b)

        if self._currentTab is not None:
            self._rois[self._currentTab].setVisible(b)

        self._imageItem.setVisible(b)

    def setTracker(self, group_name: str, index: int):
        for roi in self._currentShapeGroup[group_name].shapes:
            self.removeItem(roi)

        self._currentShapeGroup[group_name] = self._shapeGroups[group_name][
            index
        ]

        for roi in self._currentShapeGroup[group_name].shapes:
            self.addItem(roi)
            roi.setBBox(self._rois[group_name].bbox)

    def clearShapes(self):
        for name, shapeGroups in self._shapeGroups.items():
            for shapeGroup in shapeGroups:
                for shape in shapeGroup.shapes:
                    self.removeItem(shape)

    def addTrackerGroup(self, group_name: str, trackers: Iterable[Tracker]):
        roi = self.addRoi(group_name)
        self._shapeGroups[group_name] = [
            ShapeGroup.fromTracker(i) for i in trackers
        ]

        for tracker in trackers:
            tracker.roi = roi.bbox

        roi.sigRegionChanged.connect(lambda: self.roiChanged.emit(group_name))
        self._currentShapeGroup[group_name] = self._shapeGroups[group_name][0]
        self.setTracker(group_name, 0)

    def setTrackerGroup(self, name: str):
        self._setCurrentRoi(name)
        for shape_groups in self._shapeGroups.values():
            for shape_group in shape_groups:
                shape_group.setZValue(1)

        self._currentShapeGroup[name].setZValue(2)

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

    def setRect(self, rect):
        self._bbox.value = rect
        self.setPos(self._pos)
        self._bbox.value = rect
        self.setSize(self._size)

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

    def setZValue(self, value):
        for shape in self.shapes:
            shape.setZValue(value)

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
        return GuiEllipse(shape)
    elif isinstance(shape, Points):
        return PgPoints(shape)
    else:
        raise NotImplementedError


class ShapeMixin:
    @abstractmethod
    def refresh(self):
        pass

    @abstractmethod
    def setBBox(self, bbox):
        pass


class PgPoints(pg.ScatterPlotItem, ShapeMixin):
    def __init__(self, points: Points):
        super().__init__()
        self._points = points
        self.setPen(points.lc, width=points.lw)
        self.setSymbol(points.symbol)
        self.refresh()

    def refresh(self):
        if self._points.visible:
            self.setVisible(True)
            self.setData(pos=self._points.data)
        else:
            self.setVisible(False)

    def setBBox(self, bbox):
        self._points.set_bbox(bbox)


class GuiEllipse(QtWidgets.QGraphicsEllipseItem, ShapeMixin):
    def __init__(self, ellipse: Ellipse):
        super().__init__()
        self._ellipse = ellipse
        self.setPen(pg.mkPen(color=ellipse.lc, width=ellipse.lw))
        self.refresh()

    def setBBox(self, bbox):
        self._ellipse.set_bbox(bbox)

    def refresh(self):
        if self._ellipse.visible:
            cx = self._ellipse.cx
            cy = self._ellipse.cy
            a = self._ellipse.a
            b = self._ellipse.b
            theta = self._ellipse.theta
            self.setVisible(True)
            self.setRect(cx - a, cy - b, a * 2, b * 2)
            self.setTransformOriginPoint(cx, cy)
            self.setRotation(theta)
        else:
            self.setVisible(False)
