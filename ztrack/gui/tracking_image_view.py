import pyqtgraph as pg
from PyQt5 import QtWidgets


class TrackingPlotWidget(pg.PlotWidget):
    def __init__(self, parent: QtWidgets.QWidget = None):
        super().__init__(parent)
        pg.setConfigOptions(imageAxisOrder="row-major")
        self._imageItem = pg.ImageItem()
        self.addItem(self._imageItem)
        self.invertY(True)
        self.setAspectLocked(1)
        self.hideAxis("bottom")
        self.hideAxis("left")
        self.setBackground(None)

    def setImage(self, img):
        self._imageItem.setImage(img)
