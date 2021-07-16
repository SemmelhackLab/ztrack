from PyQt5 import QtWidgets


class ControlWidget(QtWidgets.QTabWidget):
    def __init__(self, parent: QtWidgets.QWidget = None):
        super().__init__(parent)

    def addTracker(self):
        pass


if __name__ == "__main__":
    from ztrack.gui.utils.launch import launch

    launch(ControlWidget)
