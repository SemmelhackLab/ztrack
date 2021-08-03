from abc import abstractmethod
from typing import Type

from PyQt5 import QtCore, QtWidgets

from ztrack.utils.variable import (Angle, AngleDeg180, AngleDeg360, Float, Int,
                                   Point, Variable)


class VariableWidget(QtWidgets.QWidget):
    def __init__(
        self, parent: QtWidgets.QWidget = None, *, variable: Variable
    ):
        super().__init__(parent)
        self._variable = variable

    @staticmethod
    def fromVariable(variable: Variable, parent: QtWidgets.QWidget = None):
        if isinstance(variable, Int):
            return IntWidget(parent, variable=variable)
        if isinstance(variable, Float):
            return FloatWidget(parent, variable=variable)
        if isinstance(variable, Point):
            return PointWidget(parent, variable=variable)
        if isinstance(variable, AngleDeg360):
            return Angle360Widget(parent, variable=variable)
        if isinstance(variable, AngleDeg180):
            return Angle180Widget(parent, variable=variable)
        raise NotImplementedError

    @abstractmethod
    def setValue(self, value):
        pass

    @property
    @abstractmethod
    def valueChanged(self):
        pass


class AngleWidget(VariableWidget):
    def __init__(
        self,
        parent: QtWidgets.QWidget = None,
        *,
        variable: Angle,
        dial: Type[QtWidgets.QDial] = None,
    ):
        super().__init__(parent, variable=variable)

        self._qDial = QtWidgets.QDial(self) if dial is None else dial(self)
        self._qDial.setWrapping(True)
        self._qDial.setMinimum(0)
        self._qDial.setNotchesVisible(True)
        self._qDial.setNotchTarget(90)

        self._spinBox = QtWidgets.QSpinBox(self)
        self._spinBox.setMinimum(0)

        layout = QtWidgets.QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._qDial)
        layout.addWidget(self._spinBox)
        self.setLayout(layout)

    def _onValueChanged(self, value: int):
        self._variable.value = value

    def setValue(self, value):
        self._spinBox.setValue(value)

    @property
    def valueChanged(self):
        return self._spinBox.valueChanged


class Angle360Widget(AngleWidget):
    def __init__(
        self, parent: QtWidgets.QWidget = None, *, variable: AngleDeg360
    ):
        super().__init__(parent, variable=variable)

        self._qDial.setMaximum(359)
        self._qDial.setValue((int(variable.value) - 90) % 360)

        self._spinBox.setMaximum(359)
        self._spinBox.setValue(int(variable.value))
        self._spinBox.setWrapping(True)

        self._qDial.valueChanged.connect(
            lambda x: self._spinBox.setValue((x + 90) % 360)
        )
        self._spinBox.valueChanged.connect(
            lambda x: self._qDial.setValue((x - 90) % 360)
        )
        self._spinBox.valueChanged.connect(self._onValueChanged)


class Angle180Widget(AngleWidget):
    class MyDial(QtWidgets.QDial):
        def sliderChange(
            self, change: QtWidgets.QAbstractSlider.SliderChange
        ) -> None:
            if change == QtWidgets.QAbstractSlider.SliderValueChange:
                value = self.value()
                if value > 180:
                    self.setValue(180)
            super().sliderChange(change)

    def __init__(
        self, parent: QtWidgets.QWidget = None, *, variable: AngleDeg180
    ):
        super().__init__(parent, variable=variable, dial=Angle180Widget.MyDial)

        self._qDial.setMaximum(360)
        self._qDial.setValue(int(variable.value))

        self._spinBox.setMaximum(180)
        self._spinBox.setValue(int(variable.value))

        self._qDial.valueChanged.connect(lambda x: self._spinBox.setValue(x))
        self._spinBox.valueChanged.connect(lambda x: self._qDial.setValue(x))
        self._spinBox.valueChanged.connect(self._onValueChanged)


class PointWidget(VariableWidget):
    _valueChanged = QtCore.pyqtSignal()
    pointSelectionModeChanged = QtCore.pyqtSignal(bool)

    def setValue(self, value):
        x, y = value
        self._label.setText(f"({x}, {y})")
        self._variable.value = value

    def __init__(self, parent: QtWidgets.QWidget = None, *, variable: Point):
        super().__init__(parent, variable=variable)

        self._pointSelectionMode = False

        self._pushButton = QtWidgets.QPushButton(self)
        self._pushButton.setText("Select point")

        self._label = QtWidgets.QLabel(self)

        if variable.value is not None:
            x, y = variable.value
            self._label.setText(f"({x}, {y})")

        layout = QtWidgets.QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._pushButton)
        layout.addWidget(self._label)
        self.setLayout(layout)

        self._pushButton.clicked.connect(self._onPushButtonClicked)

    def setPoint(self, x, y):
        self.setValue((x, y))
        self._setPointSelectionMode(False)
        self._valueChanged.emit()

    def _setPointSelectionMode(self, b):
        self._pointSelectionMode = b
        if self._pointSelectionMode:
            self._pushButton.setText("Cancel")
        else:
            self._pushButton.setText("Select point")
        self.pointSelectionModeChanged.emit(self._pointSelectionMode)

    def _onPushButtonClicked(self):
        self._setPointSelectionMode(not self._pointSelectionMode)

    @property
    def valueChanged(self) -> QtCore.pyqtBoundSignal:
        return self._valueChanged


class FloatWidget(VariableWidget):
    def __init__(self, parent: QtWidgets.QWidget = None, *, variable: Float):
        super().__init__(parent, variable=variable)

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
        super().__init__(parent, variable=variable)

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
