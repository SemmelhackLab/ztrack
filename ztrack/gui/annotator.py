from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING

import pandas as pd
from PyQt5 import QtGui, QtWidgets, QtCore

from ztrack.gui.utils.file import selectVideoDirectories, selectVideoPaths
from ztrack.tracking import get_trackers_from_config
from ztrack.utils.file import (
    get_config_path,
    get_paths_for_view_results,
    get_results_path,
    video_extensions,
)

from ._main_window import MainWindow

if TYPE_CHECKING:
    from typing import Dict, List

    from ztrack.tracking.tracker import Tracker


class Annotator(MainWindow):
    def __init__(
        self,
        parent: QtWidgets.QWidget = None,
        videoPaths: List[str] = None,
        verbose=False,
        dock=False,
        update=True,
    ):
        super().__init__(
            parent, videoPaths=videoPaths, verbose=verbose, dock=dock
        )

        self._results: Dict[str, pd.DataFrame] = {}
        self._trackers: Dict[str, Tracker] = {}

        self._buttonBox = QtWidgets.QDialogButtonBox(self)
        self._buttonBox.setStandardButtons(
            QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel  # type: ignore
        )
        self._layout.addWidget(self._buttonBox)

        self._buttonBox.button(QtWidgets.QDialogButtonBox.Ok).clicked.connect(
            self._onOkButtonClicked
        )

        self._buttonBox.button(QtWidgets.QDialogButtonBox.Cancel).clicked.connect(
            self._onCancelButtonClicked
        )

        self.buffer = []

        if update:
            self.updateVideo()

    def keyPressEvent(self, event):
        Key = QtCore.Qt.Key

        def key2string(key):
            if key in range(Key.Key_0, Key.Key_9 + 1):
                return chr(key)
            elif key in range(Key.Key_A, Key.Key_Z):
                return chr(key)

        if self._currentVideoPath is not None:
            if event.key() == Key.Key_Backspace:
                if self.buffer:
                    self.buffer.pop()
            else:
                key = key2string(event.key())
                if key is not None:
                    thing = (self._frameBar.value(), key)
                    if thing not in self.buffer:
                        self.buffer.append(thing)

            print(self.buffer)

        event.accept()

    def _onOkButtonClicked(self):
        csv_path = self._currentVideoPath.replace("mp4", "csv")
        pd.DataFrame(self.buffer, columns=["frame", "type"]).to_csv(csv_path, index=False)
        self.buffer.clear()
        self.dequeue()
        self.updateVideo()

    def _onCancelButtonClicked(self):
        self.dequeue()
        self.updateVideo()

    def dropEvent(self, event: QtGui.QDropEvent) -> None:
        paths = [u.toLocalFile() for u in event.mimeData().urls()]
        paths = [path for path in paths if Path(path).suffix in video_extensions]
        paths = sorted(paths)

        for path in paths[::-1]:
            self.enqueue(str(path), first=True)

        self.updateVideo()

    def _onFrameChanged(self):
        img = self._currentFrame

        if img is not None:
            self._trackingPlotWidget.setImage(img)

    def enqueue(self, videoPath: str, first=False):
        if first:
            self._videoPaths.insert(0, videoPath)
        else:
            self._videoPaths.append(videoPath)

    def dequeue(self):
        if len(self._videoPaths) > 0:
            self._videoPaths.pop(0)
            # self._savePaths.pop(0)

    def _openFiles(self):
        videoPaths = selectVideoPaths(native=True)

        for videoPath in reversed(videoPaths):
            self.enqueue(videoPath, first=True)

        self.updateVideo()

    def _openFolders(self):
        directories, (recursive,) = selectVideoDirectories(
            (("Include subdirectories", True),)
        )
        videoPaths = get_paths_for_view_results(
            directories,
            recursive,
        )

        for videoPath in videoPaths:
            self.enqueue(videoPath)

        self.updateVideo()

    def updateVideo(self):
        self._trackingPlotWidget.clearShapes()

        if self._currentVideoPath is not None:
            results_path = get_results_path(self._currentVideoPath)
            config_path = get_config_path(self._currentVideoPath)

            if results_path.exists() and config_path.exists():
                store = pd.HDFStore(results_path)

                for key in store.keys():
                    self._results[key.lstrip("/")] = pd.DataFrame(
                        store.get(key)
                    )

                with open(config_path) as fp:
                    config_dict = json.load(fp)
                self._trackers = get_trackers_from_config(config_dict)

                for name, tracker in self._trackers.items():
                    self._trackingPlotWidget.addTrackerGroup(name, [tracker])
                store.close()

        super().updateVideo()

    def dragEnterEvent(self, event: QtGui.QDragEnterEvent) -> None:
        if event.mimeData().hasUrls():
            paths = [u.toLocalFile() for u in event.mimeData().urls()]

            if all(
                [
                    Path(path).suffix in video_extensions
                    for path in paths
                ]
            ):
                event.accept()
        else:
            event.ignore()
