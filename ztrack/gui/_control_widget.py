from __future__ import annotations

from typing import TYPE_CHECKING

from PyQt5 import QtCore, QtWidgets

from ztrack.gui.utils.variable_widgets import PointWidget, VariableWidget, RectWidget

if TYPE_CHECKING:
    from typing import Dict, Iterable, List

    from ztrack.gui.create_config import CreateConfigWindow
    from ztrack.tracking.tracker import Tracker
    from ztrack.utils.typing import config_dict, params_dict


class ControlWidget(QtWidgets.QTabWidget):
    trackerChanged = QtCore.pyqtSignal(str, int)
    paramsChanged = QtCore.pyqtSignal(str, int)

    def __init__(self, parent: CreateConfigWindow):
        super().__init__(parent)

        self._trackingPlotWidget = parent.trackingPlotWidget
        self._tabs: Dict[str, TrackingTab] = {}

    @property
    def trackingPlotWidget(self):
        return self._trackingPlotWidget

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

    def setStateFromTrackingConfig(self, trackingConfig: config_dict):
        for groupName, groupDict in trackingConfig.items():
            self._tabs[groupName].setState(
                groupDict["method"], groupDict["params"]
            )


class TrackingTab(QtWidgets.QWidget):
    def __init__(self, parent: ControlWidget, groupName: str):
        super().__init__(parent)

        self._trackingPlotWidget = parent.trackingPlotWidget
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
    def trackingPlotWidget(self):
        return self._trackingPlotWidget

    @property
    def trackerIndexChanged(self) -> QtCore.pyqtBoundSignal:
        return self._comboBox.currentIndexChanged

    @property
    def currentIndex(self):
        return self._comboBox.currentIndex()

    def setTracker(self, i: int):
        self._paramsStackWidget.setCurrentIndex(i)

    def setState(self, methodName: str, params: params_dict):
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

    def __init__(self, parent: TrackingTab, *, tracker: Tracker):
        super().__init__(parent)
        self._trackingPlotWidget = parent.trackingPlotWidget
        self._formLayout = QtWidgets.QFormLayout()
        self.setLayout(self._formLayout)
        self._fields: Dict[str, VariableWidget] = {}

        for name, param in zip(
            tracker.params.parameter_names, tracker.params.parameter_list
        ):
            label = QtWidgets.QLabel(self)
            label.setText(param.display_name)
            field = VariableWidget.fromVariable(param, self)

            if isinstance(field, (PointWidget, RectWidget)):
                field.setTrackingPlotWidget(self._trackingPlotWidget)

            field.valueChanged.connect(self.paramsChanged.emit)
            self._fields[name] = field
            self._formLayout.addRow(label, field)

    def setParams(self, params: params_dict):
        for name, value in params.items():
            self._fields[name].setValue(value)
