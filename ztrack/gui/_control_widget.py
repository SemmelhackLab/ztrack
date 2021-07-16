from PyQt5 import QtWidgets


class ControlWidget(QtWidgets.QTabWidget):
    def __init__(self, parent: QtWidgets.QWidget = None):
        super().__init__(parent)
        self.addTrackingTab("Eye")

    def addTrackingTab(self, name: str):
        tab = TrackingTab(self)
        self.addTab(tab, name)


class TrackingTab(QtWidgets.QWidget):
    def __init__(self, parent: QtWidgets.QWidget = None):
        super().__init__(parent)


if __name__ == "__main__":
    from ztrack.gui.utils.launch import launch

    launch(ControlWidget)
