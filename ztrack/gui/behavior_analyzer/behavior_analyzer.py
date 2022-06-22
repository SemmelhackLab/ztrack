from typing import List

from PyQt5 import QtCore, QtWidgets

from ztrack.gui.behavior_analyzer.control_widget import ControlWidget
from ztrack.gui.behavior_analyzer.plot_widget import PlotWidget
from ztrack.gui.tracking_viewer import TrackingViewer
from ztrack.gui.utils.launch import launch


class BehaviorAnalyzer(TrackingViewer):
    def __init__(
        self,
        parent: QtWidgets.QWidget = None,
        videoPaths: List[str] = None,
        verbose=False,
    ):
        super(BehaviorAnalyzer, self).__init__(
            parent, videoPaths, verbose, dock=True, update=False
        )

        self.plotDockWidget = QtWidgets.QDockWidget(self)
        self.plotWidget = PlotWidget(self.plotDockWidget)
        self.plotDockWidget.setWidget(self.plotWidget)

        self.addDockWidget(QtCore.Qt.DockWidgetArea(2), self.plotDockWidget)

        self.controlDockWidget = QtWidgets.QDockWidget(self)
        self.controlDockWidget.setWidget(ControlWidget(self.controlDockWidget))
        self.addDockWidget(QtCore.Qt.DockWidgetArea(2), self.controlDockWidget)

        self.updateVideo()

    def updateVideo(self):
        super().updateVideo()
        if self._currentVideoPath is not None:
            self.plotWidget.plot(df_eye=self._results["eye"])

    def _onFrameChanged(self):
        super(BehaviorAnalyzer, self)._onFrameChanged()
        # self.plotWidget.axvline(self._frameBar.value())


if __name__ == "__main__":
    launch(BehaviorAnalyzer, videoPaths=[r"D:\hsc\20220330-F4\T1-b.avi"])
