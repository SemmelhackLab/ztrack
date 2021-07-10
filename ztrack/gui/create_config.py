from typing import List, Optional

from decord import VideoReader
from PyQt5 import QtCore, QtWidgets

from ztrack.gui._control_widget import ControlWidget
from ztrack.gui._tracking_display_widget import TrackingDisplayWidget
from ztrack.gui.utils.file import selectVideoDirectories, selectVideoPaths
from ztrack.gui.utils.frame_bar import FrameBar
from ztrack.utils.file import extract_video_paths
from ztrack.utils.config import video_extensions, config_extension


class CreateConfigWidget(QtWidgets.QWidget):
    def __init__(self, parent: QtWidgets.QWidget = None):
        super().__init__(parent)

        self._frameBar = FrameBar(self)
        self._controlWidget = ControlWidget(self)
        self._trackingDisplayWidget = TrackingDisplayWidget(self)

        self._buttonBox = QtWidgets.QDialogButtonBox(self)
        self._buttonBox.setStandardButtons(
            QtWidgets.QDialogButtonBox.Apply  # type: ignore
            | QtWidgets.QDialogButtonBox.Cancel
        )

        hBoxLayout1 = QtWidgets.QHBoxLayout()
        hBoxLayout1.setContentsMargins(0, 0, 0, 0)
        hBoxLayout1.addWidget(self._trackingDisplayWidget)
        hBoxLayout1.addWidget(self._controlWidget)
        hBoxLayout1.setStretch(0, 50)
        hBoxLayout1.setStretch(1, 50)

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self._frameBar)
        layout.addLayout(hBoxLayout1)
        layout.addWidget(self._buttonBox)

        self.setLayout(layout)

    @property
    def fps(self):
        return self._frameBar.fps

    @fps.setter
    def fps(self, fps: int):
        self._frameBar.fps = fps


class CreateConfigWindow(QtWidgets.QMainWindow):
    def __init__(self, parent: QtWidgets.QWidget = None):
        super().__init__(parent)
        self._useVideoFPS = True

        self._videoPaths: List[str] = []
        self._savePaths: List[List[str]] = []

        self._currentVideoPath: Optional[str] = None
        self._currentSavePaths: Optional[List[str]] = None

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
        self._centralWidget = CreateConfigWidget(self)
        self.setCentralWidget(self._centralWidget)
        self.setWindowState(QtCore.Qt.WindowMaximized)

        actionOpenFiles.triggered.connect(self._openFiles)
        actionOpenFolders.triggered.connect(self._openFolders)
        actionSetFPS.triggered.connect(self._setFPS)

    @property
    def _fps(self):
        return self._centralWidget.fps

    @_fps.setter
    def _fps(self, fps: int):
        self._centralWidget.fps = fps

    def _setFPS(self):
        def onCheckBoxStateChange(state: int):
            isEnabled = state == 0
            spinBox.setEnabled(isEnabled)
            label.setEnabled(isEnabled)

        def onAccepted():
            self._useVideoFPS = checkBox.isChecked()
            if not self._useVideoFPS:
                self._fps = spinBox.value()
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
        spinBox.setValue(self._fps)

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

        dialog.exec()

    def _reset(self):
        pass

    def _triggerCreateConfig(self):
        if len(self._videoPaths) == 0:
            self._reset()
            return

        self._currentVideoPath = self._videoPaths.pop(0)
        self._currentSavePaths = self._savePaths.pop(0)
        self._videoReader = VideoReader(self._currentVideoPath)

    def _enqueue(self, videoPath: str, savePaths: List[str]):
        self._videoPaths.append(videoPath)
        self._savePaths.append(savePaths)

    def _openFiles(self):
        videoPaths = selectVideoPaths(native=True)
        for videoPath in videoPaths:
            self._enqueue(videoPath, [videoPath])
        self._triggerCreateConfig()

    def _openFolders(self):
        (
            directories,
            recursive,
            sameConfig,
            overwrite,
        ) = selectVideoDirectories()
        videoPaths, savePaths = extract_video_paths(
            directories, recursive, sameConfig, overwrite, config_extension,
            video_extensions
        )
        self._videoPaths.extend(videoPaths)
        self._savePaths.extend(savePaths)
        self._triggerCreateConfig()


if __name__ == "__main__":
    from ztrack.gui.utils.launch import launch

    launch(CreateConfigWindow)
