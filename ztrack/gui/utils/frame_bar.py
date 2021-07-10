from PyQt5 import QtCore, QtWidgets
from PyQt5.QtWidgets import QStyle


class FrameBar(QtWidgets.QWidget):
    def __init__(self, parent: QtWidgets.QWidget = None):
        super().__init__(parent)

        self._fps = 100
        self._playTimer = QtCore.QTimer()
        self._playTimer.setInterval(int(1000 / self._fps))

        self._playing = False
        self._playIcon = self.style().standardIcon(QStyle.SP_MediaPlay)
        self._pauseIcon = self.style().standardIcon(QStyle.SP_MediaPause)
        self._pushButton = QtWidgets.QPushButton(self)
        self._pushButton.setIcon(self._playIcon)

        self._slider = QtWidgets.QSlider(self)
        self._slider.setOrientation(QtCore.Qt.Horizontal)

        self._spinBox = QtWidgets.QSpinBox(self)

        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._pushButton)
        layout.addWidget(self._slider)
        layout.addWidget(self._spinBox)

        self.setLayout(layout)

        self._slider.valueChanged.connect(self._spinBox.setValue)
        self._spinBox.valueChanged.connect(self._slider.setValue)
        self._playTimer.timeout.connect(self._playTick)
        self._pushButton.clicked.connect(self._onPushButtonClicked)

        self.setMaximum(3000)

    @property
    def fps(self):
        return self._fps

    @fps.setter
    def fps(self, fps: int):
        self._fps = fps
        self._playTimer.setInterval(int(1000 / fps))

    def setMaximum(self, value: int):
        self._slider.setMaximum(value)
        self._spinBox.setMaximum(value)

    def _onPushButtonClicked(self):
        self._playing = not self._playing

        if self._playing:
            self._play()
        else:
            self._pause()

    def _play(self):
        self._pushButton.setIcon(self._pauseIcon)
        self._playTimer.start()

    def _pause(self):
        self._pushButton.setIcon(self._playIcon)
        self._playTimer.stop()

    def _playTick(self):
        value = (self._slider.value() + 1) % self._slider.maximum()
        self._slider.setValue(value)
