from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from PyQt5 import QtWidgets

from ztrack.gui.behavior_analyzer.multirow import MultiRowAxes


class PlotWidget(QtWidgets.QWidget):
    def __init__(self, parent: QtWidgets.QWidget = None, fps=200):
        super().__init__(parent)
        self._figure: plt.Figure = plt.figure()
        self._canvas = FigureCanvas(self._figure)
        self._toolbar = NavigationToolbar(self._canvas, self)

        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(self._toolbar)
        layout.addWidget(self._canvas)
        self.setLayout(layout)
        self.fps = fps
        self._axes = None

    def plot(self, df_eye):
        n_frames = len(df_eye)
        self._axes = MultiRowAxes(np.linspace(0, n_frames, 7), 1, fig=self._figure)
        ax_eye = self._axes[0]
        ax_eye.plot(df_eye[("left_eye", "angle")].values, c="b")
        ax_eye.plot(df_eye[("right_eye", "angle")].values, c="r")
        plt.tight_layout()

    def axvline(self, x):
        if self._axes is not None:
            for ax in self._axes:
                ax.axvline1(x / self.fps)
