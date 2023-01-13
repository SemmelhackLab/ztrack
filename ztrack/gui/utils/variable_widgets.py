from __future__ import annotations

from abc import ABC, ABCMeta, abstractmethod
from typing import TYPE_CHECKING

from PyQt5 import QtCore, QtWidgets
from superqt import QLabeledDoubleRangeSlider

from ztrack.utils.variable import (
    Angle,
    Bool,
    Float,
    FloatRange,
    Int,
    Point,
    Rect,
    String,
)

if TYPE_CHECKING:
    from typing import Optional

    from ztrack.gui._tracking_plot_widget import TrackingPlotWidget
    from ztrack.utils.typing import point2d, rect
    from ztrack.utils.variable import Variable


class AbstractWidgetMeta(type(QtWidgets.QWidget), ABCMeta):  # type: ignore
    pass


class VariableWidget(QtWidgets.QWidget, ABC, metaclass=AbstractWidgetMeta):
    valueChanged = QtCore.pyqtSignal()

    def __init__(self, parent: QtWidgets.QWidget = None, *, variable: Variable):
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
        if isinstance(variable, Rect):
            return RectWidget(parent, variable=variable)
        if isinstance(variable, String):
            return StringWidget(parent, variable=variable)
        if isinstance(variable, Bool):
            return BoolWidget(parent, variable=variable)
        if isinstance(variable, FloatRange):
            return FloatRangeWidget(parent, variable=variable)
        raise NotImplementedError

    def _setValue(self, value):
        self._variable.value = value
        self._setGuiValue(self._variable.value)
        self.valueChanged.emit()

    @abstractmethod
    def _setGuiValue(self, value):
        pass

    def setValue(self, value):
        self._setValue(value)
        self._setGuiValue(value)


class FloatRangeWidget(VariableWidget):
    _variable: FloatRange

    def __init__(self, parent: QtWidgets.QWidget = None, *, variable: FloatRange):
        super().__init__(parent, variable=variable)
        self._slider = QLabeledDoubleRangeSlider(self)
        self._slider.setOrientation(QtCore.Qt.Orientation.Horizontal)
        self._slider.setRange(variable.minimum, variable.maximum)
        self._slider.setValue(variable.value)

        layout = QtWidgets.QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._slider)
        self.setLayout(layout)
        self._slider.valueChanged.connect(self._setValue)

    def _setGuiValue(self, value):
        self._slider.valueChanged.disconnect()
        self._slider.setValue(value)
        self._slider.valueChanged.connect(self._setValue)


class BoolWidget(VariableWidget):
    def __init__(self, parent: QtWidgets.QWidget = None, *, variable: Bool):
        super().__init__(parent, variable=variable)

        self._checkbox = QtWidgets.QCheckBox(self)
        self._checkbox.setChecked(variable.value)

        layout = QtWidgets.QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._checkbox)
        self.setLayout(layout)

        self._checkbox.stateChanged.connect(self._setValue)

    def _setGuiValue(self, value: bool):
        self._checkbox.setChecked(value)


class StringWidget(VariableWidget):
    def __init__(self, parent: QtWidgets.QWidget = None, *, variable: String):
        super().__init__(parent, variable=variable)

        self._line = QtWidgets.QLineEdit(self)
        layout = QtWidgets.QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._line)
        self.setLayout(layout)
        self._line.editingFinished.connect(self._updateValue)

    def _updateValue(self):
        return self.setValue(self._line.text())

    def _setGuiValue(self, value):
        self._line.setText(value)


class IntWidget(VariableWidget):
    def __init__(self, parent: QtWidgets.QWidget = None, *, variable: Int):
        super().__init__(parent, variable=variable)

        self._slider = QtWidgets.QSlider(self)
        self._slider.setOrientation(QtCore.Qt.Horizontal)
        self._slider.setMinimum(variable.minimum)
        self._slider.setMaximum(variable.maximum)
        self._slider.setValue(variable.value)
        self._spinBox = QtWidgets.QSpinBox(self)
        self._spinBox.setMinimum(variable.minimum)
        self._spinBox.setMaximum(variable.maximum)
        self._spinBox.setValue(variable.value)

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
        self._spinBox.setMinimum(variable.minimum)
        self._spinBox.setMaximum(variable.maximum)
        self._spinBox.setValue(variable.value)
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
    _selectionModeChanged = QtCore.pyqtSignal(bool)
    _trackingPlotWidget: TrackingPlotWidget

    def __init__(self, parent: QtWidgets.QWidget = None, *, variable: Point):
        super().__init__(parent, variable=variable)

        self._selectionMode = False

        self._pushButton = QtWidgets.QPushButton(self)
        self._pushButton.setText(self._get_display_str(variable.value))

        layout = QtWidgets.QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._pushButton)
        self.setLayout(layout)

        self._pushButton.clicked.connect(lambda: self._setSelectionMode(not self._selectionMode))

    def _setGuiValue(self, value: point2d):
        self._pushButton.setText(self._get_display_str(value))

    @staticmethod
    def _get_display_str(value: point2d):
        x, y = value
        return f"({x}, {y})"

    def _setValue(self, value):
        super()._setValue(value)
        self._setSelectionMode(False)

    def _setSelectionMode(self, b: bool):
        self._selectionMode = b

        if self._selectionMode:
            self.link()
            self._pushButton.setText("Cancel")
        else:
            self.unlink()
            self._pushButton.setText(self._get_display_str(self._variable.value))

        self._selectionModeChanged.emit(self._selectionMode)

    def link(self):
        self._trackingPlotWidget.pointSelected.connect(lambda x, y: self._setValue((x, y)))

    def unlink(self):
        try:
            self._trackingPlotWidget.pointSelected.disconnect()
        except TypeError:
            pass

    def setTrackingPlotWidget(self, trackingPlotWidget: TrackingPlotWidget):
        self._trackingPlotWidget = trackingPlotWidget
        self._selectionModeChanged.connect(self._trackingPlotWidget.setPointSelectionModeEnabled)


class RectWidget(VariableWidget):
    _selectionModeChanged = QtCore.pyqtSignal(bool)
    _trackingPlotWidget: TrackingPlotWidget

    def __init__(self, parent: QtWidgets.QWidget = None, *, variable: Rect):
        super().__init__(parent, variable=variable)

        self._selectedPoints = -1

        self._pushButton = QtWidgets.QPushButton(self)
        self._pushButton.setText(self._get_display_str(variable.value))

        layout = QtWidgets.QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._pushButton)
        self.setLayout(layout)

        self._pushButton.clicked.connect(
            lambda: self._setSelectionState(-1 if self._selectedPoints >= 0 else 0)
        )

    def _setGuiValue(self, value: rect):
        self._pushButton.setText(self._get_display_str(value))

    @staticmethod
    def _get_display_str(value: Optional[rect] = None):
        if value is not None:
            x, y, w, h = value
            return f"({x}, {y}, {w}, {h})"
        else:
            return "Npne"

    def _setPoint(self, x_new, y_new):
        x, y, w, h = self._variable.value

        if self._selectedPoints == 0:
            x, y = x_new, y_new
        else:
            w, h = x_new - x, y_new - y

        super().setValue((x, y, w, h))

        self._setSelectionState(self._selectedPoints + 1)

    def _setSelectionState(self, b: int):
        if b >= 2:
            b = -1

        self._selectedPoints = b

        if self._selectedPoints >= 0:
            self.link()
            self._pushButton.setText("Cancel")
        else:
            self.unlink()
            self._pushButton.setText(self._get_display_str(self._variable.value))

        self._selectionModeChanged.emit(self._selectedPoints >= 0)

    def link(self):
        self._trackingPlotWidget.pointSelected.connect(self._setPoint)

    def unlink(self):
        try:
            self._trackingPlotWidget.pointSelected.disconnect()
        except TypeError:
            pass

    def setTrackingPlotWidget(self, trackingPlotWidget: TrackingPlotWidget):
        self._trackingPlotWidget = trackingPlotWidget
        self._selectionModeChanged.connect(self._trackingPlotWidget.setPointSelectionModeEnabled)
