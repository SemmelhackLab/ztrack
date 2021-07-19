from typing import Dict, Iterable

from PyQt5 import QtCore, QtWidgets

from ztrack.gui.utils.variable_widgets import VariableWidget
from ztrack.tracking.tracker import Tracker


class ControlWidget(QtWidgets.QTabWidget):
    trackerChanged = QtCore.pyqtSignal(str, int)
    paramsChanged = QtCore.pyqtSignal(str, int)

    def __init__(self, parent: QtWidgets.QWidget = None):
        super().__init__(parent)
        self._tabs: Dict[str, TrackingTab] = {}

    def addTrackerGroup(self, group_name: str, trackers: Iterable[Tracker]):
        assert group_name not in self._tabs
        tab = TrackingTab(self, group_name)
        tab.trackerIndexChanged.connect(
            lambda index: self.trackerChanged.emit(group_name, index)
        )
        for tracker in trackers:
            tab.addTracker(tracker)
        self.addTab(tab, group_name.capitalize())
        self._tabs[group_name] = tab

    def getCurrentTrackerIndex(self, group_name: str):
        return self._tabs[group_name].currentIndex


class TrackingTab(QtWidgets.QWidget):
    def __init__(self, parent: ControlWidget, group_name: str):
        super().__init__(parent)
        self._group_name = group_name

        self._comboBox = QtWidgets.QComboBox(self)
        self._paramsStackWidget = QtWidgets.QStackedWidget(self)
        label = QtWidgets.QLabel(self)
        label.setText("Method")
        formLayout = QtWidgets.QFormLayout()
        formLayout.setContentsMargins(0, 0, 0, 0)
        formLayout.addRow(label, self._comboBox)
        layout = QtWidgets.QVBoxLayout()
        layout.addLayout(formLayout)
        layout.addWidget(self._paramsStackWidget)
        self.setLayout(layout)

        self.trackerIndexChanged.connect(self.setTracker)

    @property
    def trackerIndexChanged(self) -> QtCore.pyqtBoundSignal:
        return self._comboBox.currentIndexChanged

    @property
    def currentIndex(self):
        return self._comboBox.currentIndex()

    def setTracker(self, i: int):
        self._paramsStackWidget.setCurrentIndex(i)

    def addTracker(self, tracker: Tracker):
        index = self._comboBox.count()
        self._comboBox.addItem(tracker.display_name)
        widget = ParamsWidget(self, tracker=tracker)
        widget.paramsChanged.connect(
            lambda: self._parent.paramsChanged.emit(self._group_name, index)
        )
        self._paramsStackWidget.addWidget(widget)


class ParamsWidget(QtWidgets.QFrame):
    paramsChanged = QtCore.pyqtSignal()

    def __init__(self, parent: QtWidgets.QWidget = None, *, tracker: Tracker):
        super().__init__(parent)
        self._formLayout = QtWidgets.QFormLayout()
        self.setLayout(self._formLayout)

        for param in tracker.params.parameter_list:
            label = QtWidgets.QLabel(self)
            label.setText(param.display_name)
            field = VariableWidget.fromVariable(param)
            field.valueChanged.connect(self.paramsChanged.emit)
            self._formLayout.addRow(label, field)
