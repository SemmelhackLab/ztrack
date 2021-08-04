from PyQt5 import QtCore, QtWidgets
from PyQt5.QtWidgets import QStyle


class FrameBar(QtWidgets.QWidget):
    valueChanged = QtCore.pyqtSignal(int)

    def __init__(
        self, parent: QtWidgets.QWidget = None, *, fps=100, maximum=3000
    ):
        super().__init__(parent)

        self._fps = 0
        self._isPlaying = False

        self._timer = QtCore.QTimer()
        self.setFps(fps)

        self._playIcon = self.style().standardIcon(QStyle.SP_MediaPlay)
        self._pauseIcon = self.style().standardIcon(QStyle.SP_MediaPause)
        self._pushButton = QtWidgets.QPushButton(self)
        self._pushButton.setIcon(self._playIcon)

        self._slider = QtWidgets.QSlider(self)
        self._slider.setOrientation(QtCore.Qt.Horizontal)
        self._spinBox = QtWidgets.QSpinBox(self)

        layout = QtWidgets.QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._pushButton)
        layout.addWidget(self._slider)
        layout.addWidget(self._spinBox)
        self.setLayout(layout)

        self._slider.valueChanged.connect(self._spinBox.setValue)
        self._slider.valueChanged.connect(self.valueChanged.emit)
        self._spinBox.valueChanged.connect(self._slider.setValue)
        self._spinBox.valueChanged.connect(self.valueChanged.emit)

        self._timer.timeout.connect(self._playTick)
        self._pushButton.clicked.connect(self._onPushButtonClicked)

        self.setMaximum(maximum)

    def fps(self):
        return self._fps

    def setFps(self, fps: int):
        self._fps = fps
        self._timer.setInterval(int(1000 / fps))

    def setMaximum(self, value: int):
        self._slider.setMaximum(value)
        self._spinBox.setMaximum(value)

    def value(self):
        return self._slider.value()

    @QtCore.pyqtSlot()
    def _onPushButtonClicked(self):
        self._isPlaying = not self._isPlaying
        if self._isPlaying:
            self._pushButton.setIcon(self._pauseIcon)
            self._timer.start()
        else:
            self._pushButton.setIcon(self._playIcon)
            self._timer.stop()

    @QtCore.pyqtSlot()
    def _playTick(self):
        self._slider.setValue((self._slider.value() + 1) % self._slider.maximum())
