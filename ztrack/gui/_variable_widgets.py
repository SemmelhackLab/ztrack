from abc import abstractmethod

from PyQt5 import QtCore, QtWidgets

from ztrack.tracking.variable import Float, Int, Variable


class VariableWidget(QtWidgets.QWidget):
    def __init__(self, parent: QtWidgets.QWidget = None):
        super().__init__(parent)

    @staticmethod
    def fromVariable(variable: Variable, parent: QtWidgets.QWidget = None):
        if isinstance(variable, Int):
            return IntWidget(parent, variable=variable)
        elif isinstance(variable, Float):
            return FloatWidget(parent, variable=variable)
        else:
            raise NotImplementedError

    @property
    @abstractmethod
    def valueChanged(self):
        pass


class FloatWidget(VariableWidget):
    def __init__(self, parent: QtWidgets.QWidget = None, *, variable: Float):
        super().__init__(parent)
        self._spinBox = QtWidgets.QDoubleSpinBox(self)
        self._variable = variable

        layout = QtWidgets.QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._spinBox)
        self.setLayout(layout)

        self._spinBox.setValue(variable.value)
        self._spinBox.setMinimum(variable.minimum)
        self._spinBox.setMaximum(variable.maximum)
        self._spinBox.setSingleStep(variable.step)

    def _onValueChanged(self, value):
        self._variable.value = value

    @property
    def valueChanged(self):
        return self._spinBox.valueChanged


class IntWidget(VariableWidget):
    def __init__(self, parent: QtWidgets.QWidget = None, *, variable: Int):
        super().__init__(parent)
        self._slider = QtWidgets.QSlider(self)
        self._slider.setOrientation(QtCore.Qt.Horizontal)
        self._spinBox = QtWidgets.QSpinBox(self)

        layout = QtWidgets.QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._slider)
        layout.addWidget(self._spinBox)
        self.setLayout(layout)

        self._variable = variable

        self._slider.setValue(variable.value)
        self._spinBox.setValue(variable.value)

        self._slider.setMinimum(variable.minimum)
        self._spinBox.setMinimum(variable.minimum)
        self._slider.setMaximum(variable.maximum)
        self._spinBox.setMaximum(variable.maximum)

        self._slider.valueChanged.connect(self._spinBox.setValue)
        self._spinBox.valueChanged.connect(self._slider.setValue)
        self._slider.valueChanged.connect(self._onValueChanged)

    @property
    def valueChanged(self):
        return self._slider.valueChanged

    def _onValueChanged(self, value):
        self._variable.value = value
