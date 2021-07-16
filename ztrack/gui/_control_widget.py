from typing import List

from PyQt5 import QtCore, QtWidgets

from ztrack.tracking.eye.binary import BinaryEyeTracker
from ztrack.tracking.eye.multi_threshold import MultiThresholdEyeTracker
from ztrack.tracking.tracker import Tracker
from ztrack.tracking.variable import Float, Int, Variable


class ControlWidget(QtWidgets.QTabWidget):
    def __init__(self, parent: QtWidgets.QWidget = None):
        super().__init__(parent)
        self.addTrackingTab(
            "Eye", [BinaryEyeTracker(), MultiThresholdEyeTracker()]
        )

    def addTrackingTab(self, name: str, trackers: List[Tracker]):
        tab = TrackingTab(self)
        for tracker in trackers:
            tab.addTracker(tracker)
        self.addTab(tab, name)


class TrackingTab(QtWidgets.QWidget):
    def __init__(self, parent: QtWidgets.QWidget = None):
        super().__init__(parent)
        self._comboBox = QtWidgets.QComboBox(self)
        self._paramsStackWidget = ParamsStackedWidget(self)
        label = QtWidgets.QLabel(self)
        label.setText("Method")
        formLayout = QtWidgets.QFormLayout()
        formLayout.setContentsMargins(0, 0, 0, 0)
        formLayout.addRow(label, self._comboBox)
        layout = QtWidgets.QVBoxLayout()
        layout.addLayout(formLayout)
        layout.addWidget(self._paramsStackWidget)
        self.setLayout(layout)
        self._comboBox.currentIndexChanged.connect(self.setTracker)

    def setTracker(self, i: int):
        self._paramsStackWidget.setCurrentIndex(i)

    def addTracker(self, tracker: Tracker):
        self._comboBox.addItem(tracker.display_name)
        self._paramsStackWidget.addTracker(tracker)


class ParamsStackedWidget(QtWidgets.QStackedWidget):
    def __init__(self, parent: QtWidgets.QWidget = None):
        super().__init__(parent)

    def addTracker(self, tracker: Tracker):
        widget = ParamsWidget(self)
        widget.setTracker(tracker)
        self.addWidget(widget)


class ParamsWidget(QtWidgets.QWidget):
    def __init__(self, parent: QtWidgets.QWidget = None):
        super().__init__(parent)
        self._formLayout = QtWidgets.QFormLayout()
        self.setLayout(self._formLayout)

    def setTracker(self, tracker: Tracker):
        for param in tracker.params.parameter_list:
            label = QtWidgets.QLabel(self)
            label.setText(param.display_name)
            field = VariableWidget.fromVariable(param)
            self._formLayout.addRow(label, field)


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

        self._slider.setValue(variable.value)
        self._spinBox.setValue(variable.value)

        self._slider.setMinimum(variable.minimum)
        self._spinBox.setMinimum(variable.minimum)
        self._slider.setMaximum(variable.maximum)
        self._spinBox.setMaximum(variable.maximum)

        self._slider.valueChanged.connect(self._spinBox.setValue)
        self._spinBox.valueChanged.connect(self._slider.setValue)


class FloatWidget(VariableWidget):
    def __init__(self, parent: QtWidgets.QWidget = None, *, variable: Float):
        super().__init__(parent)
        self._spinBox = QtWidgets.QDoubleSpinBox(self)

        layout = QtWidgets.QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._spinBox)
        self.setLayout(layout)

        self._spinBox.setValue(variable.value)
        self._spinBox.setMinimum(variable.minimum)
        self._spinBox.setMaximum(variable.maximum)
        self._spinBox.setSingleStep(variable.step)


if __name__ == "__main__":
    from ztrack.gui.utils.launch import launch

    launch(ControlWidget)
