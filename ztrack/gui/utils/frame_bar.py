from PyQt5 import QtCore, QtWidgets
from PyQt5.QtWidgets import QStyle


class FrameBar(QtWidgets.QWidget):
    def __init__(self, parent: QtWidgets.QWidget = None):
        super().__init__(parent)

        self._fps = 100
        self._isPlaying = False
        self._timer = QtCore.QTimer()
        self._timer.setInterval(self._fpsToInterval(self._fps))
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
        self._spinBox.valueChanged.connect(self._slider.setValue)
        self._timer.timeout.connect(self._playTick)
        self._pushButton.clicked.connect(self._onPushButtonClicked)

        self.maximum = 3000

    @staticmethod
    def _fpsToInterval(fps: int):
        return int(1000 / fps)

    @property
    def valueChanged(self) -> QtCore.pyqtBoundSignal:
        return self._slider.valueChanged

    @property
    def fps(self):
        return self._fps

    @fps.setter
    def fps(self, fps: int):
        self._fps = fps
        self._timer.setInterval(self._fpsToInterval(fps))

    @property
    def maximum(self):
        return self._slider.maximum()

    @maximum.setter
    def maximum(self, value: int):
        self._slider.setMaximum(value)
        self._spinBox.setMaximum(value)

    @property
    def value(self):
        return self._slider.value()

    @value.setter
    def value(self, value: int):
        self._slider.setValue(value)

    def _onPushButtonClicked(self):
        self._isPlaying = not self._isPlaying
        return self._play() if self._isPlaying else self._pause()

    def _play(self):
        self._pushButton.setIcon(self._pauseIcon)
        self._timer.start()

    def _pause(self):
        self._pushButton.setIcon(self._playIcon)
        self._timer.stop()

    def _playTick(self):
        self.value = (self.value + 1) % self.maximum
