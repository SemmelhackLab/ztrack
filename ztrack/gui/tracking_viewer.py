import json
from pathlib import Path
from typing import Dict, List

import pandas as pd
from PyQt5 import QtGui, QtWidgets

from ztrack.gui.utils.file import selectVideoDirectories, selectVideoPaths
from ztrack.tracking import get_trackers_from_config
from ztrack.tracking.tracker import Tracker
from ztrack.utils.file import (get_config_path, get_paths_for_view_results,
                               get_results_path, video_extensions)

from ._main_window import MainWindow


class TrackingViewer(MainWindow):
    def __init__(
        self,
        parent: QtWidgets.QWidget = None,
        videoPaths: List[str] = None,
        verbose=False,
    ):
        super().__init__(parent, videoPaths=videoPaths, verbose=verbose)
        self._results: Dict[str, pd.DataFrame] = {}
        self._trackers: Dict[str, Tracker] = {}
        self.updateVideo()

    def dropEvent(self, event: QtGui.QDropEvent) -> None:
        paths = [u.toLocalFile() for u in event.mimeData().urls()]
        for path in paths:
            self.enqueue(str(path), first=True)
        self.updateVideo()

    def _onFrameChanged(self):
        img = self._currentFrame
        if img is not None:
            self._trackingPlotWidget.setImage(img)
            for name, tracker in self._trackers.items():
                tracker.annotate_from_series(
                    self._results[name].iloc[self._frameBar.value]
                )
                self._trackingPlotWidget.updateRoiGroups()

    def enqueue(self, videoPath: str, first=False):
        if first:
            self._videoPaths.insert(0, videoPath)
        else:
            self._videoPaths.append(videoPath)

    def dequeue(self):
        if len(self._videoPaths) > 0:
            self._videoPaths.pop(0)
            self._savePaths.pop(0)

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
                    and get_config_path(path).exists()
                    and get_results_path(path).exists()
                    for path in paths
                ]
            ):
                event.accept()
        else:
            event.ignore()
