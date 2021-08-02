from abc import abstractmethod
from traceback import print_stack

from PyQt5 import QtCore, QtWidgets

from ztrack.utils.variable import Float, Int, Variable, Point


class VariableWidget(QtWidgets.QWidget):
    def __init__(self, parent: QtWidgets.QWidget = None):
        super().__init__(parent)

    @staticmethod
    def fromVariable(variable: Variable, parent: QtWidgets.QWidget = None):
        if isinstance(variable, Int):
            return IntWidget(parent, variable=variable)
        if isinstance(variable, Float):
            return FloatWidget(parent, variable=variable)
        if isinstance(variable, Point):
            return PointWidget(parent, variable=variable)
        raise NotImplementedError

    @abstractmethod
    def setValue(self, value):
        pass

    @property
    @abstractmethod
    def valueChanged(self) -> QtCore.pyqtBoundSignal:
        pass


class PointWidget(VariableWidget):
    _valueChanged = QtCore.pyqtSignal()

    def setValue(self, value):
        self._line_edit.setText(str(value))

    def __init__(self, parent: QtWidgets.QWidget = None, *, variable: Point):
        super().__init__(parent)
        self._variable = variable
        self._spinBoxX = QtWidgets.QSpinBox(self)
        self._spinBoxY = QtWidgets.QSpinBox(self)
        self._spinBoxX.setMaximum(1000)
        self._spinBoxY.setMaximum(1000)
        x, y = variable.value
        self._spinBoxX.setValue(x)
        self._spinBoxY.setValue(y)

        layout = QtWidgets.QHBoxLayout()
        layout.addWidget(self._spinBoxX)
        layout.addWidget(self._spinBoxY)
        self.setLayout(layout)

        self._spinBoxX.valueChanged.connect(self._onValueChanged)
        self._spinBoxY.valueChanged.connect(self._onValueChanged)

    def _onValueChanged(self):
        self._variable.value = (self._spinBoxX.value(), self._spinBoxY.value())
        self._valueChanged.emit()

    @property
    def valueChanged(self) -> QtCore.pyqtBoundSignal:
        return self._valueChanged


class FloatWidget(VariableWidget):
    def __init__(self, parent: QtWidgets.QWidget = None, *, variable: Float):
        super().__init__(parent)
        self._variable = variable

        self._spinBox = QtWidgets.QDoubleSpinBox(self)
        self._spinBox.setValue(variable.value)
        self._spinBox.setMinimum(variable.minimum)
        self._spinBox.setMaximum(variable.maximum)
        self._spinBox.setSingleStep(variable.step)

        layout = QtWidgets.QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._spinBox)
        self.setLayout(layout)

        self._spinBox.valueChanged.connect(self._onValueChanged)

    def _onValueChanged(self, value: float):
        self._variable.value = value

    def setValue(self, value: float):
        self._spinBox.setValue(value)

    @property
    def valueChanged(self):
        return self._spinBox.valueChanged


class IntWidget(VariableWidget):
    def __init__(self, parent: QtWidgets.QWidget = None, *, variable: Int):
        super().__init__(parent)
        self._variable = variable

        self._slider = QtWidgets.QSlider(self)
        self._slider.setOrientation(QtCore.Qt.Horizontal)
        self._slider.setValue(variable.value)
        self._slider.setMinimum(variable.minimum)
        self._slider.setMaximum(variable.maximum)
        self._spinBox = QtWidgets.QSpinBox(self)
        self._spinBox.setValue(variable.value)
        self._spinBox.setMinimum(variable.minimum)
        self._spinBox.setMaximum(variable.maximum)

        layout = QtWidgets.QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._slider)
        layout.addWidget(self._spinBox)
        self.setLayout(layout)

        self._slider.valueChanged.connect(self._spinBox.setValue)
        self._spinBox.valueChanged.connect(self._slider.setValue)
        self._slider.valueChanged.connect(self._onValueChanged)

    def setValue(self, value: int):
        self._slider.setValue(value)

    @property
    def valueChanged(self):
        return self._slider.valueChanged

    def _onValueChanged(self, value: int):
        self._variable.value = value
