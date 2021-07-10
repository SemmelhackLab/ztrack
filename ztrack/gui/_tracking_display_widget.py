import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from PyQt5 import QtWidgets

plt.rcParams["axes.facecolor"] = (0, 0, 0, 0)
plt.rcParams["figure.facecolor"] = (0, 0, 0, 0)


class TrackingDisplayWidget(QtWidgets.QFrame):
    def __init__(self, parent: QtWidgets.QWidget = None):
        super().__init__(parent)
        self.__figure = plt.figure()
        self.__canvas = FigureCanvasQTAgg(self.__figure)
        self.setStyleSheet("border: 1px solid")

        layout = QtWidgets.QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.__canvas)
        self.setLayout(layout)
