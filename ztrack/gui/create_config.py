from typing import List, Optional

from decord import VideoReader
from PyQt5 import QtCore, QtWidgets

from ztrack._settings import config_extension, video_extensions
from ztrack.gui._control_widget import ControlWidget
from ztrack.gui._tracking_image_view import TrackingPlotWidget
from ztrack.gui.utils.file import selectVideoDirectories, selectVideoPaths
from ztrack.gui.utils.frame_bar import FrameBar
from ztrack.tracking import get_trackers
from ztrack.tracking.tracker import Tracker
from ztrack.utils.file import extract_video_paths


class CreateConfigWindow(QtWidgets.QMainWindow):
    def __init__(
            self,
            parent: QtWidgets.QWidget = None,
            videoPaths: List[str] = None,
            savePaths: List[List[str]] = None,
            verbose=False,
    ):
        super().__init__(parent)
        if videoPaths is None:
            videoPaths = []
        if savePaths is None:
            savePaths = []

        self._videoPaths: List[str] = videoPaths
        self._savePaths: List[List[str]] = savePaths
        self._verbose = verbose

        self._useVideoFPS = True
        self._videoReader = None

        self._currentVideoPath: Optional[str] = None
        self._currentSavePaths: Optional[List[str]] = None

        self._trackers = get_trackers()

        self._frameBar = FrameBar(self)
        self._controlWidget = ControlWidget(self)
        self._trackingImageView = TrackingPlotWidget(self)

        self._buttonBox = QtWidgets.QDialogButtonBox(self)
        self._buttonBox.setStandardButtons(
            QtWidgets.QDialogButtonBox.Apply  # type: ignore
            | QtWidgets.QDialogButtonBox.Cancel
        )

        hBoxLayout1 = QtWidgets.QHBoxLayout()
        hBoxLayout1.setContentsMargins(0, 0, 0, 0)
        hBoxLayout1.addWidget(self._trackingImageView)
        hBoxLayout1.addWidget(self._controlWidget)
        hBoxLayout1.setStretch(0, 50)
        hBoxLayout1.setStretch(1, 50)

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self._frameBar)
        layout.addLayout(hBoxLayout1)
        layout.addWidget(self._buttonBox)

        widget = QtWidgets.QWidget(self)
        widget.setLayout(layout)
        self.setCentralWidget(widget)

        menuBar = self.menuBar()

        actionOpenFiles = QtWidgets.QAction(self)
        actionOpenFiles.setText("&Open Files")
        actionOpenFiles.setShortcut("Ctrl+O")

        actionOpenFolders = QtWidgets.QAction(self)
        actionOpenFolders.setText("&Open Folders")
        actionOpenFolders.setShortcut("Ctrl+Shift+O")

        actionSetFPS = QtWidgets.QAction(self)
        actionSetFPS.setText("&Set FPS")

        actionAbout = QtWidgets.QAction(self)
        actionAbout.setText("&About")
        actionHelp = QtWidgets.QAction(self)
        actionHelp.setText("&Help")

        fileMenu = menuBar.addMenu("&File")
        viewMenu = menuBar.addMenu("&View")
        helpMenu = menuBar.addMenu("&Help")

        fileMenu.addAction(actionOpenFiles)
        fileMenu.addAction(actionOpenFolders)
        viewMenu.addAction(actionSetFPS)
        helpMenu.addAction(actionAbout)
        helpMenu.addAction(actionHelp)

        self.setMenuBar(menuBar)
        self.setWindowTitle("ztrack")

        actionOpenFiles.triggered.connect(self._openFiles)
        actionOpenFolders.triggered.connect(self._openFolders)
        actionSetFPS.triggered.connect(self._setFPS)

        for k, v in self._trackers.items():
            self._addTrackerGroup(k, v)
        self._trackingImageView.setTrackerGroup(list(self._trackers)[0])

        self._frameBar.valueChanged.connect(self._onFrameChanged)
        self._controlWidget.currentChanged.connect(self._onTabChanged)
        self._controlWidget.trackerChanged.connect(self._onTrackerChanged)
        self._controlWidget.paramsChanged.connect(self._onParamsChanged)
        self._trackingImageView.roiChanged.connect(self._onRoiChanged)

        self.triggerCreateConfig()

    @property
    def _currentFrame(self):
        if self._videoReader is None:
            return None
        return self._videoReader[self._frameBar.value].asnumpy()

    def _onFrameChanged(self):
        img = self._currentFrame
        if img is not None:
            self._trackingImageView.setImage(img)
            for name, tracker in self._trackers.items():
                index = self._controlWidget.getCurrentTrackerIndex(name)
                tracker[index].annotate(img)
                self._trackingImageView.updateRoiGroups()

    def _onTrackerChanged(self, name: str, index: int):
        self._trackingImageView.setTracker(name, index)
        img = self._currentFrame
        if img is not None:
            self._trackers[name][index].annotate(self._currentFrame)
            self._trackingImageView.updateRoiGroups()

    def _onRoiChanged(self, name: str):
        img = self._currentFrame
        if img is not None:
            index = self._controlWidget.getCurrentTrackerIndex(name)
            self._trackers[name][index].annotate(img)
            self._trackingImageView.updateRoiGroups()

    def _onTabChanged(self, index: int):
        name = list(self._trackers)[index]
        self._trackingImageView.setTrackerGroup(name)

    def _onParamsChanged(self, name: str, index: int):
        img = self._currentFrame
        if img is not None:
            self._trackers[name][index].annotate(img)
            self._trackingImageView.updateRoiGroups()

    def _addTrackerGroup(self, name: str, trackers: List[Tracker]):
        self._controlWidget.addTrackerGroup(name, trackers)
        self._trackingImageView.addTrackerGroup(name, trackers)

    def _setFPS(self):
        def onCheckBoxStateChange(state: int):
            isEnabled = state == 0
            spinBox.setEnabled(isEnabled)
            label.setEnabled(isEnabled)

        def onAccepted():
            self._useVideoFPS = checkBox.isChecked()
            if not self._useVideoFPS:
                self._frameBar.fps = spinBox.value()
            else:
                if self._videoReader is not None:
                    self._frameBar.fps = int(self._videoReader.get_avg_fps())
            dialog.close()

        def onRejected():
            dialog.close()

        dialog = QtWidgets.QDialog(None)
        dialog.setWindowFlags(QtCore.Qt.WindowTitleHint)
        dialog.setWindowTitle("Set FPS")
        label = QtWidgets.QLabel(dialog)
        label.setText("FPS")
        spinBox = QtWidgets.QSpinBox(dialog)
        spinBox.setMinimum(0)
        spinBox.setMaximum(1000)
        spinBox.setValue(self._frameBar.fps)

        formLayout = QtWidgets.QFormLayout()
        formLayout.addRow(label, spinBox)

        checkBox = QtWidgets.QCheckBox(dialog)
        checkBox.setText("Use video FPS")

        buttonBox = QtWidgets.QDialogButtonBox(dialog)
        buttonBox.setStandardButtons(
            QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel
        )

        layout = QtWidgets.QVBoxLayout()
        layout.addLayout(formLayout)
        layout.addWidget(checkBox)
        layout.addWidget(buttonBox)
        dialog.setLayout(layout)
        dialog.setMinimumWidth(300)

        checkBox.stateChanged.connect(onCheckBoxStateChange)
        buttonBox.accepted.connect(onAccepted)
        buttonBox.rejected.connect(onRejected)

        checkBox.setChecked(self._useVideoFPS)

        dialog.exec()

    def _updateVideo(self):
        if self._currentVideoPath is not None:
            self._videoReader = VideoReader(self._currentVideoPath)
            self._frameBar.maximum = len(self._videoReader) - 1
            if self._useVideoFPS:
                self._frameBar.fps = int(self._videoReader.get_avg_fps())
            self._onFrameChanged()
            h, w = self._videoReader[0].shape[:2]
            self._trackingImageView.setRoiDefaultSize(w, h)
            rect = QtCore.QRectF(0, 0, w, h)
            self._trackingImageView.setRoiMaxBounds(rect)

    def triggerCreateConfig(self):
        if len(self._videoPaths) == 0:
            self._currentVideoPath = None
            self._currentSavePaths = None
        else:
            self._currentVideoPath = self._videoPaths.pop(0)
            self._currentSavePaths = self._savePaths.pop(0)

        self._updateVideo()

    def enqueue(self, videoPath: str, savePaths: List[str]):
        self._videoPaths.append(videoPath)
        self._savePaths.append(savePaths)

    def _openFiles(self):
        videoPaths = selectVideoPaths(native=True)
        for videoPath in videoPaths:
            self.enqueue(videoPath, [videoPath])
        self.triggerCreateConfig()

    def _openFolders(self):
        (
            directories,
            recursive,
            sameConfig,
            overwrite,
        ) = selectVideoDirectories()
        videoPaths, savePaths = extract_video_paths(
            directories,
            recursive,
            sameConfig,
            overwrite,
            config_extension,
            video_extensions,
        )
        self._videoPaths.extend(videoPaths)
        self._savePaths.extend(savePaths)
        self.triggerCreateConfig()
