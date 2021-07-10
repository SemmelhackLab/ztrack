from PyQt5 import QtCore, QtWidgets


class IntSlider(QtWidgets.QWidget):
    clicked = QtCore.pyqtSignal()

    def __init__(self, parent: QtWidgets.QWidget = None):
        super().__init__(parent)

        self._slider = QtWidgets.QSlider(self)
        self._slider.setOrientation(QtCore.Qt.Horizontal)
        self._spinBox = QtWidgets.QSpinBox(self)

        layout = QtWidgets.QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._slider)
        layout.addWidget(self._spinBox)
        self.setLayout(layout)

        self._slider.valueChanged.connect(self._spinBox.setValue)
        self._spinBox.valueChanged.connect(self._slider.setValue)

    @property
    def valueChanged(self):
        return self._slider.valueChanged

    def value(self):
        return self._slider.value()

    def setValue(self, value: int):
        return self._slider.setValue(value)

    def maximum(self):
        return self._slider.maximum()

    def increment(self):
        self.setValue((self.value() + 1) % self.maximum())


if __name__ == "__main__":
    from ztrack.gui.utils.launch import launch

    launch(IntSlider)
