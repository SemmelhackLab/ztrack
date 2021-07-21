from typing import Dict, Iterable, List

from PyQt5 import QtCore, QtWidgets

from ztrack.gui.utils.variable_widgets import VariableWidget
from ztrack.tracking.tracker import Tracker


class ControlWidget(QtWidgets.QTabWidget):
    trackerChanged = QtCore.pyqtSignal(str, int)
    paramsChanged = QtCore.pyqtSignal(str, int)

    def __init__(self, parent: QtWidgets.QWidget = None):
        super().__init__(parent)
        self._tabs: Dict[str, TrackingTab] = {}

    def addTrackerGroup(self, groupName: str, trackers: Iterable[Tracker]):
        assert groupName not in self._tabs
        tab = TrackingTab(self, groupName)
        tab.trackerIndexChanged.connect(
            lambda index: self.trackerChanged.emit(groupName, index)
        )
        for tracker in trackers:
            tab.addTracker(tracker)
        self.addTab(tab, groupName.capitalize())
        self._tabs[groupName] = tab

    def getCurrentTrackerIndex(self, groupName: str):
        return self._tabs[groupName].currentIndex

    def setStateFromTrackingConfig(self, trackingConfig: dict):
        for groupName, groupDict in trackingConfig.items():
            self._tabs[groupName].setState(
                groupDict["method"], groupDict["params"]
            )


class TrackingTab(QtWidgets.QWidget):
    def __init__(self, parent: ControlWidget, groupName: str):
        super().__init__(parent)
        self._parent = parent
        self._groupName = groupName
        self._trackers: List[Tracker] = []
        self._trackerNames: List[str] = []
        self._paramsWidgets: List[ParamsWidget] = []
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

    def setState(self, methodName: str, params: dict):
        index = self._trackerNames.index(methodName)
        self._comboBox.setCurrentIndex(index)
        self._paramsWidgets[index].setParams(params)

    def addTracker(self, tracker: Tracker):
        self._trackerNames.append(tracker.name())
        self._trackers.append(tracker)
        index = self._comboBox.count()
        self._comboBox.addItem(tracker.display_name())
        widget = ParamsWidget(self, tracker=tracker)
        widget.paramsChanged.connect(
            lambda: self._parent.paramsChanged.emit(self._groupName, index)
        )
        self._paramsWidgets.append(widget)
        self._paramsStackWidget.addWidget(widget)


class ParamsWidget(QtWidgets.QFrame):
    paramsChanged = QtCore.pyqtSignal()

    def __init__(self, parent: QtWidgets.QWidget = None, *, tracker: Tracker):
        super().__init__(parent)
        self._formLayout = QtWidgets.QFormLayout()
        self.setLayout(self._formLayout)
        self._fields: Dict[str, VariableWidget] = {}

        for name, param in zip(
            tracker.params.parameter_names, tracker.params.parameter_list
        ):
            label = QtWidgets.QLabel(self)
            label.setText(param.display_name)
            field = VariableWidget.fromVariable(param)
            field.valueChanged.connect(self.paramsChanged.emit)
            self._fields[name] = field
            self._formLayout.addRow(label, field)

    def setParams(self, params: dict):
        for name, value in params.items():
            self._fields[name].setValue(value)
