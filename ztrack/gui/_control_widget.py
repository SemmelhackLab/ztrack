from typing import Dict, List

from PyQt5 import QtWidgets

from ztrack.gui._variable_widgets import VariableWidget
from ztrack.tracking.tracker import Tracker


class ControlWidget(QtWidgets.QTabWidget):
    def __init__(self, parent: QtWidgets.QWidget = None):
        super().__init__(parent)
        self._tabs: Dict[str, TrackingTab] = {}

    def addTrackerGroup(self, name: str, trackers: List[Tracker]):
        tab = TrackingTab(self)
        for tracker in trackers:
            tab.addTracker(tracker)
        self.addTab(tab, name)
        self._tabs[name] = tab

    def getTrackerIndex(self, name):
        return self._tabs[name].currentIndex


class TrackingTab(QtWidgets.QWidget):
    def __init__(self, parent: QtWidgets.QWidget = None):
        super().__init__(parent)
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
        self._comboBox.currentIndexChanged.connect(self.setTracker)

    @property
    def currentIndex(self):
        return self._comboBox.currentIndex()

    def setTracker(self, i: int):
        self._paramsStackWidget.setCurrentIndex(i)

    def addTracker(self, tracker: Tracker):
        self._comboBox.addItem(tracker.display_name)
        widget = ParamsWidget(self, tracker=tracker)
        self._paramsStackWidget.addWidget(widget)


class ParamsWidget(QtWidgets.QWidget):
    def __init__(self, parent: QtWidgets.QWidget = None, *, tracker: Tracker):
        super().__init__(parent)
        self._formLayout = QtWidgets.QFormLayout()
        self.setLayout(self._formLayout)

        for param in tracker.params.parameter_list:
            label = QtWidgets.QLabel(self)
            label.setText(param.display_name)
            field = VariableWidget.fromVariable(param)
            self._formLayout.addRow(label, field)


if __name__ == "__main__":
    from ztrack.gui.utils.launch import launch

    launch(ControlWidget)
