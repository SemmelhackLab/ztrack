from __future__ import annotations

from abc import ABC, ABCMeta, abstractmethod
from typing import TYPE_CHECKING

from PyQt5 import QtCore, QtWidgets

from ztrack.utils.variable import Angle, Float, Int, Point

if TYPE_CHECKING:
    from ztrack.gui._tracking_plot_widget import TrackingPlotWidget
    from ztrack.utils.typing import point2d
    from ztrack.utils.variable import Variable


class AbstractWidgetMeta(type(QtWidgets.QWidget), ABCMeta):  # type: ignore
    pass


class VariableWidget(QtWidgets.QWidget, ABC, metaclass=AbstractWidgetMeta):
    valueChanged = QtCore.pyqtSignal()

    def __init__(
        self, parent: QtWidgets.QWidget = None, *, variable: Variable
    ):
        super().__init__(parent)
        self._variable = variable

    @staticmethod
    def fromVariable(variable: Variable, parent: QtWidgets.QWidget = None):
        if isinstance(variable, Angle):
            return AngleWidget(parent, variable=variable)
        if isinstance(variable, Float):
            return FloatWidget(parent, variable=variable)
        if isinstance(variable, Int):
            return IntWidget(parent, variable=variable)
        if isinstance(variable, Point):
            return PointWidget(parent, variable=variable)
        raise NotImplementedError

    def _setValue(self, value):
        self._variable.value = value
        self.valueChanged.emit()

    @abstractmethod
    def _setGuiValue(self, value):
        pass

    def setValue(self, value):
        self._setValue(value)
        self._setGuiValue(value)


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

        self._slider.valueChanged.connect(self._setValue)
        self._spinBox.valueChanged.connect(self._setValue)

    def _setGuiValue(self, value: int):
        self._spinBox.setValue(value)
        self._slider.setValue(value)


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

        self._spinBox.valueChanged.connect(self._setValue)

    def _setGuiValue(self, value: float):
        self._spinBox.setValue(value)


class AngleWidget(VariableWidget):
    class CompassDial(QtWidgets.QDial):
        _valueChanged = QtCore.pyqtSignal(int)

        def __init__(self, parent: QtWidgets.QWidget = None, *, rotation=-90):
            super().__init__(parent)

            self._rotation = rotation
            self.setMinimum(0)
            self.setMaximum(359)
            self.setWrapping(True)
            self.setNotchesVisible(True)
            self.setNotchTarget(90)

            super().valueChanged.connect(
                lambda x: self._valueChanged.emit((x - self._rotation) % 360)
            )

        @property
        def valueChanged(self):
            return self._valueChanged

        def setValue(self, a0: int) -> None:
            super().setValue((a0 + self._rotation) % 360)

    def __init__(
        self,
        parent: QtWidgets.QWidget = None,
        *,
        variable: Angle,
        rotation=-90,
    ):
        super().__init__(parent, variable=variable)

        self._compassDial = AngleWidget.CompassDial(self, rotation=rotation)
        self._spinBox = QtWidgets.QSpinBox(self)
        self._spinBox.setMinimum(0)

        layout = QtWidgets.QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._compassDial)
        layout.addWidget(self._spinBox)
        self.setLayout(layout)

        self._compassDial.setValue(int(variable.value))
        self._spinBox.setMaximum(359)
        self._spinBox.setValue(int(variable.value))
        self._spinBox.setWrapping(True)

        self._compassDial.valueChanged.connect(self._spinBox.setValue)
        self._spinBox.valueChanged.connect(self._compassDial.setValue)

        self._compassDial.valueChanged.connect(self._setValue)
        self._spinBox.valueChanged.connect(self._setValue)

    def _setGuiValue(self, value: int):
        self._spinBox.setValue(value)
        self._compassDial.setValue(value)


class PointWidget(VariableWidget):
    _pointSelectionModeChanged = QtCore.pyqtSignal(bool)

    def __init__(self, parent: QtWidgets.QWidget = None, *, variable: Point):
        super().__init__(parent, variable=variable)

        self._pointSelectionMode = False

        self._pushButton = QtWidgets.QPushButton(self)
        self._pushButton.setText(self._get_display_str(variable.value))

        layout = QtWidgets.QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._pushButton)
        self.setLayout(layout)

        self._pushButton.clicked.connect(
            lambda: self._setPointSelectionMode(not self._pointSelectionMode)
        )

    def _setGuiValue(self, value: point2d):
        self._pushButton.setText(self._get_display_str(value))

    @staticmethod
    def _get_display_str(value: point2d):
        x, y = value
        return f"({x}, {y})"

    def _setPoint(self, x: int, y: int):
        self._setValue((x, y))
        self._setPointSelectionMode(False)

    def _setPointSelectionMode(self, b: bool):
        self._pointSelectionMode = b

        if self._pointSelectionMode:
            self._pushButton.setText("Cancel")
        else:
            self._pushButton.setText(
                self._get_display_str(self._variable.value)
            )

        self._pointSelectionModeChanged.emit(self._pointSelectionMode)

    def link(self, trackingPlotWidget: TrackingPlotWidget):
        self._pointSelectionModeChanged.connect(
            trackingPlotWidget.setPointSelectionModeEnabled
        )
        trackingPlotWidget.pointSelected.connect(self._setPoint)
