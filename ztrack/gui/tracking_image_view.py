from typing import List
import pyqtgraph as pg
from PyQt5 import QtWidgets


class TrackingPlotWidget(pg.PlotWidget):
    def __init__(self, parent: QtWidgets.QWidget = None):
        super().__init__(parent)
        pg.setConfigOptions(imageAxisOrder="row-major")
        self._imageItem = pg.ImageItem()
        self._rois: List[pg.RectROI] = []
        self._currentROI = None
        self.addItem(self._imageItem)
        self.invertY(True)
        self.setAspectLocked(1)
        self.hideAxis("bottom")
        self.hideAxis("left")
        self.setBackground(None)

    def addROI(self):
        roi = pg.RectROI((0, 0), (100, 100), rotatable=False, movable=False,
                         resizable=False)
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
