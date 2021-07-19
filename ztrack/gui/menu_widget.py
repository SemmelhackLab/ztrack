import webbrowser
from typing import Optional

from PyQt5 import QtCore, QtGui, QtWidgets

from ztrack.gui.create_config import CreateConfigWindow
from ztrack.metadata import homepage, version


class MenuWidget(QtWidgets.QWidget):
    def __init__(self, parent: QtWidgets.QWidget = None):
        super().__init__(parent)
        self._createConfigWindow: Optional[CreateConfigWindow] = None
        self.resize(400, 300)
        self.gridLayout = QtWidgets.QGridLayout(self)
        spacerItem = QtWidgets.QSpacerItem(
            40,
            20,
            QtWidgets.QSizePolicy.Expanding,
            QtWidgets.QSizePolicy.Minimum,
        )
        self.gridLayout.addItem(spacerItem, 1, 0, 1, 1)
        spacerItem1 = QtWidgets.QSpacerItem(
            20,
            40,
            QtWidgets.QSizePolicy.Minimum,
            QtWidgets.QSizePolicy.Expanding,
        )
        self.gridLayout.addItem(spacerItem1, 2, 1, 1, 1)
        spacerItem2 = QtWidgets.QSpacerItem(
            20,
            40,
            QtWidgets.QSizePolicy.Minimum,
            QtWidgets.QSizePolicy.Expanding,
        )
        self.gridLayout.addItem(spacerItem2, 0, 1, 1, 1)
        self.verticalLayout = QtWidgets.QVBoxLayout()
        self.zFishTrackLabel = QtWidgets.QLabel(self)
        sizePolicy = QtWidgets.QSizePolicy(
            QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred
        )
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(
            self.zFishTrackLabel.sizePolicy().hasHeightForWidth()
        )
        self.zFishTrackLabel.setSizePolicy(sizePolicy)
        self.zFishTrackLabel.setMaximumSize(QtCore.QSize(16777215, 16777215))
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(36)
        self.zFishTrackLabel.setFont(font)
        self.zFishTrackLabel.setScaledContents(True)
        self.zFishTrackLabel.setAlignment(QtCore.Qt.AlignCenter)
        self.verticalLayout.addWidget(self.zFishTrackLabel)
        self.versionLabel = QtWidgets.QLabel(self)
        self.versionLabel.setText("")
        self.versionLabel.setAlignment(
            QtCore.Qt.AlignRight    # type: ignore
            | QtCore.Qt.AlignTrailing
            | QtCore.Qt.AlignVCenter
        )
        self.verticalLayout.addWidget(self.versionLabel)
        self.createConfigPushButton = QtWidgets.QPushButton(self)
        self.verticalLayout.addWidget(self.createConfigPushButton)
        self.runTrackingPushButton = QtWidgets.QPushButton(self)
        self.verticalLayout.addWidget(self.runTrackingPushButton)
        self.viewResultsPushButton = QtWidgets.QPushButton(self)
        self.verticalLayout.addWidget(self.viewResultsPushButton)
        self.helpPushButton = QtWidgets.QPushButton(self)
        self.verticalLayout.addWidget(self.helpPushButton)
        self.gridLayout.addLayout(self.verticalLayout, 1, 1, 1, 1)
        spacerItem3 = QtWidgets.QSpacerItem(
            40,
            20,
            QtWidgets.QSizePolicy.Expanding,
            QtWidgets.QSizePolicy.Minimum,
        )
        self.gridLayout.addItem(spacerItem3, 1, 2, 1, 1)
        self.action_Help = QtWidgets.QAction(self)

        self.setWindowTitle("ztrack")
        self.zFishTrackLabel.setText("ztrack")
        self.createConfigPushButton.setText("Create config")
        self.runTrackingPushButton.setText("Run tracking")
        self.viewResultsPushButton.setText("View results")
        self.helpPushButton.setText("Help")
        self.action_Help.setText("&Help")

        self.versionLabel.setText(f"v{version}")

        self.createConfigPushButton.clicked.connect(
            self._onCreateConfigPushButtonClicked
        )
        self.runTrackingPushButton.clicked.connect(
            self._onRunTrackingPushButtonClicked
        )
        self.viewResultsPushButton.clicked.connect(
            self._onViewResultsPushButtonClicked
        )
        print(homepage)
        self.helpPushButton.clicked.connect(lambda: webbrowser.open(homepage))

    @property
    def createConfigWindow(self) -> Optional[CreateConfigWindow]:
        return self._createConfigWindow

    @createConfigWindow.setter
    def createConfigWindow(self, value: Optional[CreateConfigWindow]):
        if value is None:
            self._createConfigWindow = None
            self.setEnabled(True)
        else:
            self._createConfigWindow = value
            self.setEnabled(False)

    def _onCreateConfigPushButtonClicked(self):
        self.createConfigWindow = CreateConfigWindow()
        self.createConfigWindow.closedSignal.connect(
            self._onCreateConfigWindowClosed
        )
        self.createConfigWindow.showMaximized()

    def _onCreateConfigWindowClosed(self):
        self.createConfigWindow = None

    def _onRunTrackingPushButtonClicked(self):
        pass

    def _onViewResultsPushButtonClicked(self):
        pass


def main():
    from ztrack.gui.utils.launch import launch
    launch(MenuWidget, windowState=QtCore.Qt.WindowNoState)
