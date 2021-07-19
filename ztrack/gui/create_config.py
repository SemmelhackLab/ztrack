import json
from pathlib import Path
from typing import List, Optional

from decord import VideoReader
from PyQt5 import QtCore, QtGui, QtWidgets

from ztrack._settings import config_extension, video_extensions
from ztrack.gui._control_widget import ControlWidget
from ztrack.gui._tracking_image_view import TrackingPlotWidget
from ztrack.gui.utils.file import selectVideoDirectories, selectVideoPaths
from ztrack.gui.utils.frame_bar import FrameBar
from ztrack.tracking import get_trackers
from ztrack.tracking.tracker import Tracker
from ztrack.utils.file import extract_video_paths


class CreateConfigWindow(QtWidgets.QMainWindow):
    closedSignal = QtCore.pyqtSignal()

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

        self._trackerGroups = get_trackers()

        self._frameBar = FrameBar(self)
        self._controlWidget = ControlWidget(self)
        self._trackingImageView = TrackingPlotWidget(self)

        self._buttonBox = QtWidgets.QDialogButtonBox(self)
        self._buttonBox.setStandardButtons(
            QtWidgets.QDialogButtonBox.Ok  # type: ignore
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
        self.setAcceptDrops(True)

        actionOpenFiles.triggered.connect(self._openFiles)
        actionOpenFolders.triggered.connect(self._openFolders)
        actionSetFPS.triggered.connect(self._setFPS)

        for k, v in self._trackerGroups.items():
            self._addTrackerGroup(k, v)
        self._trackingImageView.setTrackerGroup(list(self._trackerGroups)[0])

        self._frameBar.valueChanged.connect(self._onFrameChanged)
        self._controlWidget.currentChanged.connect(self._onTabChanged)
        self._controlWidget.trackerChanged.connect(self._onTrackerChanged)
        self._controlWidget.paramsChanged.connect(self._onParamsChanged)
        self._trackingImageView.roiChanged.connect(self._onRoiChanged)
        self._buttonBox.button(
            QtWidgets.QDialogButtonBox.Cancel
        ).clicked.connect(self._onCancelButtonClicked)
        self._buttonBox.button(QtWidgets.QDialogButtonBox.Ok).clicked.connect(
            self._onOkButtonClicked
        )
        self._setEnabled(False)
        self.updateVideo()

    @property
    def _currentVideoPath(self) -> Optional[str]:
        if len(self._videoPaths) > 0:
            return self._videoPaths[0]
        return None

    @property
    def _currentSavePaths(self) -> Optional[List[str]]:
        if len(self._savePaths) > 0:
            return self._savePaths[0]
        return None

    def _saveTrackingConfig(self):
        trackingConfig = {}
        for group_name, trackers in self._trackerGroups.items():
            tracker = trackers[
                self._controlWidget.getCurrentTrackerIndex(group_name)
            ]
            trackingConfig[group_name] = dict(
                method=tracker.name,
                roi=tracker.roi.value,
                params=tracker.params.to_dict(),
            )
        for savePath in self._currentSavePaths:
            with open(savePath + config_extension, "w") as fp:
                json.dump(trackingConfig, fp)

    def _onOkButtonClicked(self):
        self._saveTrackingConfig()
        self.dequeue()
        self.updateVideo()

    def _onCancelButtonClicked(self):
        self.dequeue()
        self.updateVideo()

    def dragEnterEvent(self, event: QtGui.QDragEnterEvent) -> None:
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event: QtGui.QDropEvent) -> None:
        paths = [u.toLocalFile() for u in event.mimeData().urls()]
        for path in paths:
            self.enqueue(path, [path], first=True)
        self.updateVideo()

    def _setEnabled(self, b: bool):
        self._trackingImageView.setEnabled(b)
        self.centralWidget().setEnabled(b)

    @property
    def _currentFrame(self):
        if self._videoReader is None:
            return None
        return self._videoReader[self._frameBar.value].asnumpy()

    def _onFrameChanged(self):
        img = self._currentFrame
        if img is not None:
            self._trackingImageView.setImage(img)
            for name, tracker in self._trackerGroups.items():
                index = self._controlWidget.getCurrentTrackerIndex(name)
                tracker[index].annotate(img)
                self._trackingImageView.updateRoiGroups()

    def _onTrackerChanged(self, name: str, index: int):
        self._trackingImageView.setTracker(name, index)
        img = self._currentFrame
        if img is not None:
            self._trackerGroups[name][index].annotate(self._currentFrame)
            self._trackingImageView.updateRoiGroups()

    def _onRoiChanged(self, name: str):
        img = self._currentFrame
        if img is not None:
            index = self._controlWidget.getCurrentTrackerIndex(name)
            self._trackerGroups[name][index].annotate(img)
            self._trackingImageView.updateRoiGroups()

    def _onTabChanged(self, index: int):
        name = list(self._trackerGroups)[index]
        self._trackingImageView.setTrackerGroup(name)

    def _onParamsChanged(self, name: str, index: int):
        img = self._currentFrame
        if img is not None:
            self._trackerGroups[name][index].annotate(img)
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

    def _setStateFromTrackingConfig(self, trackingConfig: dict):
        self._controlWidget.setStateFromTrackingConfig(trackingConfig)
        self._trackingImageView.setStateFromTrackingConfig(trackingConfig)

    def updateVideo(self):
        if self._currentVideoPath is not None:
            configPath = Path(self._currentVideoPath + config_extension)
            if configPath.exists():
                with open(configPath) as fp:
                    trackingConfig = json.load(fp)
                self._setStateFromTrackingConfig(trackingConfig)
            self._videoReader = VideoReader(self._currentVideoPath)
            self._frameBar.maximum = len(self._videoReader) - 1
            if self._useVideoFPS:
                self._frameBar.fps = int(self._videoReader.get_avg_fps())
            self._onFrameChanged()
            h, w = self._videoReader[0].shape[:2]
            self._trackingImageView.setRoiDefaultSize(w, h)
            rect = QtCore.QRectF(0, 0, w, h)
            self._trackingImageView.setRoiMaxBounds(rect)
            self._setEnabled(True)
        else:
            self._setEnabled(False)

    def enqueue(self, videoPath: str, savePaths: List[str], first=False):
        if first:
            self._videoPaths.insert(0, videoPath)
            self._savePaths.insert(0, savePaths)
        else:
            self._videoPaths.append(videoPath)
            self._savePaths.append(savePaths)

    def dequeue(self):
        if len(self._videoPaths) > 0:
            self._videoPaths.pop(0)
            self._savePaths.pop(0)

    def _openFiles(self):
        videoPaths = selectVideoPaths(native=True)
        for videoPath in reversed(videoPaths):
            self.enqueue(videoPath, [videoPath], first=True)
        self.updateVideo()

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
        for videoPath, savePath in zip(videoPaths, savePaths):
            self.enqueue(videoPath, savePath)
        self.updateVideo()

    def closeEvent(self, a0: QtGui.QCloseEvent):
        self.closedSignal.emit()
        super().closeEvent(a0)
