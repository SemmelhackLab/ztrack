from PyQt5 import QtWidgets


class ControlWidget(QtWidgets.QTabWidget):
    def __init__(self, parent: QtWidgets.QWidget = None):
        super().__init__(parent)
        self.addTab(TailTab(self), "Tail")
        self.addTab(EyesTab(self), "Eyes")


class Tab(QtWidgets.QWidget):
    def __init__(self, parent: QtWidgets.QWidget = None):
        super().__init__(parent)
        self.setLayout(QtWidgets.QVBoxLayout(self))


class TailTab(Tab):
    def __init__(self, parent: QtWidgets.QWidget = None):
        super().__init__(parent)
        # self.layout().addWidget(IntWidget(self, variable=Int("Test", 0, -100, 100)))


class EyesTab(Tab):
    def __init__(self, parent: QtWidgets.QWidget = None):
        super().__init__(parent)
