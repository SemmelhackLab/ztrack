from __future__ import annotations

import webbrowser
from typing import TYPE_CHECKING

from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QSizePolicy, QSpacerItem

from ztrack._run_tracking import run_tracking
from ztrack.gui.create_config import CreateConfigWindow
from ztrack.gui.utils.file import selectVideoDirectories
from ztrack.metadata import homepage, version

from .tracking_viewer import TrackingViewer

if TYPE_CHECKING:
    from typing import Optional

    from ._main_window import MainWindow


class MenuWidget(QtWidgets.QWidget):
    def __init__(self, parent: QtWidgets.QWidget = None, *, verbose=0):
        super().__init__(parent)
        self._verbose = verbose
        self._window: Optional[MainWindow] = None
        self.resize(400, 300)
        self.setWindowTitle("ztrack")

        spacerItem = QSpacerItem(
            40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum
        )
        spacerItem1 = QSpacerItem(
            20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding
        )
        spacerItem2 = QSpacerItem(
            20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding
        )
        spacerItem3 = QSpacerItem(
            40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum
        )

        label = QtWidgets.QLabel(self)
        sizePolicy = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(label.sizePolicy().hasHeightForWidth())
        label.setSizePolicy(sizePolicy)
        label.setMaximumSize(QtCore.QSize(16777215, 16777215))
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(36)
        label.setFont(font)
        label.setScaledContents(True)
        label.setAlignment(QtCore.Qt.AlignCenter)
        label.setText("ztrack")

        versionLabel = QtWidgets.QLabel(self)
        versionLabel.setText("")
        versionLabel.setAlignment(
            QtCore.Qt.AlignRight  # type: ignore
            | QtCore.Qt.AlignTrailing
            | QtCore.Qt.AlignVCenter
        )

        createConfigPushButton = QtWidgets.QPushButton(self)
        runTrackingPushButton = QtWidgets.QPushButton(self)
        viewResultsPushButton = QtWidgets.QPushButton(self)
        helpPushButton = QtWidgets.QPushButton(self)

        verticalLayout = QtWidgets.QVBoxLayout()
        verticalLayout.addWidget(label)
        verticalLayout.addWidget(versionLabel)
        verticalLayout.addWidget(createConfigPushButton)
        verticalLayout.addWidget(runTrackingPushButton)
        verticalLayout.addWidget(viewResultsPushButton)
        verticalLayout.addWidget(helpPushButton)

        gridLayout = QtWidgets.QGridLayout(self)
        gridLayout.addItem(spacerItem, 1, 0, 1, 1)
        gridLayout.addItem(spacerItem1, 2, 1, 1, 1)
        gridLayout.addItem(spacerItem2, 0, 1, 1, 1)
        gridLayout.addLayout(verticalLayout, 1, 1, 1, 1)
        gridLayout.addItem(spacerItem3, 1, 2, 1, 1)

        createConfigPushButton.setText("Create config")
        runTrackingPushButton.setText("Run tracking")
        viewResultsPushButton.setText("View results")
        helpPushButton.setText("Help")

        versionLabel.setText(f"v{version}")

        createConfigPushButton.clicked.connect(
            self._onCreateConfigPushButtonClicked
        )
        runTrackingPushButton.clicked.connect(
            self._onRunTrackingPushButtonClicked
        )
        viewResultsPushButton.clicked.connect(
            self._onViewResultsPushButtonClicked
        )
        helpPushButton.clicked.connect(lambda: webbrowser.open(homepage))

    @property
    def currentWindow(self) -> Optional[MainWindow]:
        return self._window

    @currentWindow.setter
    def currentWindow(self, value: Optional[MainWindow]):
        if value is None:
            self._window = None
            self.setEnabled(True)
        else:
            self._window = value
            self.setEnabled(False)

    def _onCreateConfigPushButtonClicked(self):
        self.currentWindow = CreateConfigWindow(verbose=self._verbose)
        self.currentWindow.closedSignal.connect(self._onWindowClosed)
        self.currentWindow.showMaximized()

    def _onWindowClosed(self):
        self.currentWindow = None

    def _onRunTrackingPushButtonClicked(self):
        inputs, (recursive, overwrite) = selectVideoDirectories(
            (
                (
                    ("Include subdirectories", True),
                    ("Overwrite tracking results", True),
                )
            )
        )
        run_tracking(inputs, recursive, overwrite, self._verbose)

    def _onViewResultsPushButtonClicked(self):
        self.currentWindow = TrackingViewer()
        self.currentWindow.closedSignal.connect(self._onWindowClosed)
        self.currentWindow.showMaximized()


def main(**kwargs):
    from ztrack.gui.utils.launch import launch

    launch(MenuWidget, windowState=QtCore.Qt.WindowNoState, **kwargs)
