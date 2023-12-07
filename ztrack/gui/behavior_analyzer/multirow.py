import matplotlib.pyplot as plt
import numpy as np
from matplotlib.gridspec import GridSpec, GridSpecFromSubplotSpec


class MultiRowAxes:
    def __init__(self, xlims: np.ndarray, nrow=2, hspace=0, fig=None, **kwargs):
        if fig is None:
            fig = plt.figure(**kwargs)

        nrow0 = len(xlims) - 1

        gs = GridSpec(nrow0, 1, figure=fig)
        axes = np.empty((nrow0, nrow), dtype=object)
        for i, gs_i in enumerate(gs):
            gs_i = GridSpecFromSubplotSpec(nrow, 1, subplot_spec=gs_i, hspace=hspace)
            for j, gs_ij in enumerate(gs_i):
                axes[i, j] = fig.add_subplot(gs_ij, sharex=axes[i, j - 1], sharey=axes[i - 1, j])

        self._axes = axes
        self._multi_row_axes = [MultiRowAx(xlims, axes=axes_) for axes_ in axes.T]

        # for ax in self._axes[:, :-1].ravel():
        #     ax.axes.xaxis.set_visible(False)

    def __getitem__(self, item):
        return self._multi_row_axes[item]

    def __iter__(self):
        for ax in self._multi_row_axes:
            yield ax


class MultiRowAx:
    def __init__(self, xlims: np.ndarray, axes=None, **kwargs):
        nrow = len(xlims) - 1
        if axes is not None:
            self._axes = axes
            assert nrow == len(axes)
        else:
            self._fig, self._axes = plt.subplots(nrow, 1, **kwargs)

        for i, ax in enumerate(self._axes):
            self._axes[i].set_xlim(xlims[i : i + 2])

        self._lines = None

    def __getattribute__(self, name):
        try:
            return super().__getattribute__(name)
        except AttributeError:
            a = [ax.__getattribute__(name) for ax in self._axes]

            if all(map(callable, a)):
                return lambda *args, **kwargs: [i(*args, **kwargs) for i in a]

            return a

    def __iter__(self):
        for ax in self._axes:
            yield ax

    def __getitem__(self, item):
        return self._axes[item]

    def __len__(self):
        return len(self._axes)

    def axvline1(self, x, **kwargs):
        if self._lines is None:
            self._lines = self.axvline(x, **kwargs)
        else:
            for line in self._lines:
                line.set_xdata([x, x])
