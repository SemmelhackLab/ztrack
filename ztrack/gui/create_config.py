from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import yaml
from PyQt5 import QtWidgets

from ztrack._settings import config_extension, video_extensions
from ztrack.gui.utils.file import selectVideoDirectories, selectVideoPaths
from ztrack.tracking import get_trackers
from ztrack.tracking.tracker import NoneTracker
from ztrack.utils.file import get_config_dict, get_paths_for_config_creation

from ._control_widget import ControlWidget
from ._main_window import MainWindow

if TYPE_CHECKING:
    from typing import List, Optional

    from PyQt5 import QtGui

    from ztrack.tracking.tracker import Tracker


class CreateConfigWindow(MainWindow):
    def __init__(
        self,
        parent: QtWidgets.QWidget = None,
        videoPaths: List[str] = None,
        savePaths: List[List[str]] = None,
        verbose=False,
        bg_frames=0,
        dark_fish=-1,
    ):
        super().__init__(
            parent,
            videoPaths=videoPaths,
            verbose=verbose,
            bg_frames=bg_frames,
            dark_fish=dark_fish,
        )

        if savePaths is None:
            savePaths = []

        self._savePaths: List[List[str]] = savePaths

        self._trackerGroups = get_trackers(verbose=verbose, debug=True)
        self._controlWidget = ControlWidget(self)

        self._buttonBox = QtWidgets.QDialogButtonBox(self)
        self._buttonBox.setStandardButtons(
            QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel  # type: ignore
        )

        self._hBoxLayout.addWidget(self._controlWidget)
        self._hBoxLayout.setStretch(0, 50)
        self._hBoxLayout.setStretch(1, 50)
        self._layout.addWidget(self._buttonBox)

        for k, v in self._trackerGroups.items():
            self._addTrackerGroup(k, v)

        self._trackingPlotWidget.setTrackerGroup(list(self._trackerGroups)[0])

        self._controlWidget.currentChanged.connect(self._onTabChanged)
        self._controlWidget.trackerChanged.connect(self._onTrackerChanged)
        self._controlWidget.paramsChanged.connect(self._onParamsChanged)
        self._trackingPlotWidget.roiChanged.connect(self._onRoiChanged)

        self._buttonBox.button(QtWidgets.QDialogButtonBox.Cancel).clicked.connect(
            self._onCancelButtonClicked
        )

        self._buttonBox.button(QtWidgets.QDialogButtonBox.Ok).clicked.connect(
            self._onOkButtonClicked
        )
        self.updateVideo()

    @property
    def trackingPlotWidget(self):
        return self._trackingPlotWidget

    @property
    def _currentSavePaths(self) -> Optional[List[str]]:
        if len(self._savePaths) > 0:
            return self._savePaths[0]

        return None

    def _saveTrackingConfig(self):
        trackingConfig = {}

        for group_name, trackers in self._trackerGroups.items():
            tracker = trackers[self._controlWidget.getCurrentTrackerIndex(group_name)]
            if not isinstance(tracker, NoneTracker):
                trackingConfig[group_name] = dict(
                    method=tracker.name(),
                    roi=list(tracker.roi.value),
                    params=tracker.params.to_dict(),
                )

        for savePath in self._currentSavePaths:
            with open(Path(savePath).with_suffix(".yml"), "w") as fp:
                yaml.dump(
                    dict(
                        video=dict(bg_frames=self._bg_frames, dark_fish=self._dark_fish),
                        tracking=trackingConfig,
                    ),
                    fp,
                )

    def _onOkButtonClicked(self):
        self._saveTrackingConfig()
        self.dequeue()
        self.updateVideo()

    def _onCancelButtonClicked(self):
        self.dequeue()
        self.updateVideo()

    def dropEvent(self, event: QtGui.QDropEvent) -> None:
        paths = [u.toLocalFile() for u in event.mimeData().urls()]
        paths = [path for path in paths if Path(path).suffix in video_extensions]
        paths = sorted(paths, key=lambda x: x[::-1])

        for path in paths[::-1]:
            self.enqueue(path, [path], first=True)

        self.updateVideo()

    def _onFrameChanged(self):
        img = self._currentFrame

        if img is not None:
            self._trackingPlotWidget.setImage(img)

            for name, tracker in self._trackerGroups.items():
                index = self._controlWidget.getCurrentTrackerIndex(name)
                tracker[index].annotate(img)
                self._trackingPlotWidget.updateRoiGroups()

    def _onTrackerChanged(self, name: str, index: int):
        self._trackingPlotWidget.setTracker(name, index)
        img = self._currentFrame

        if img is not None:
            self._trackerGroups[name][index].annotate(self._currentFrame)
            self._trackingPlotWidget.updateRoiGroups()

    def _onRoiChanged(self, name: str):
        img = self._currentFrame

        if img is not None:
            index = self._controlWidget.getCurrentTrackerIndex(name)
            self._trackerGroups[name][index].annotate(img)
            self._trackingPlotWidget.updateRoiGroups()

    def _onTabChanged(self, index: int):
        name = list(self._trackerGroups)[index]
        self._trackingPlotWidget.setTrackerGroup(name)

    def _onParamsChanged(self, name: str, index: int):
        img = self._currentFrame

        if img is not None:
            self._trackerGroups[name][index].annotate(img)
            self._trackingPlotWidget.updateRoiGroups()

    def _addTrackerGroup(self, name: str, trackers: List[Tracker]):
        self._controlWidget.addTrackerGroup(name, trackers)
        self._trackingPlotWidget.addTrackerGroup(name, trackers)

    def _setStateFromTrackingConfig(self, trackingConfig: dict):
        self._controlWidget.setStateFromTrackingConfig(trackingConfig)
        self._trackingPlotWidget.setStateFromTrackingConfig(trackingConfig)

    def updateVideo(self):
        kw = {}
        trackingConfig = {}
        if self._currentVideoPath is not None:
            config_dict = get_config_dict(self._currentVideoPath)
            if isinstance(config_dict, dict):
                trackingConfig = config_dict.get("tracking", {})
                kw = config_dict.get("video", {})

            if trackingConfig is not None:
                self._setStateFromTrackingConfig(trackingConfig)

        for tracker_group in self._trackerGroups.values():
            for tracker in tracker_group:
                tracker.set_video(self._currentVideoPath)

        super().updateVideo(**kw)

    def enqueue(self, videoPath: str, savePaths: List[str], first=False):
        if first:
            self._videoPaths.insert(0, videoPath)
            self._savePaths.insert(0, savePaths)
        else:
            self._videoPaths.append(videoPath)
            self._savePaths.append(savePaths)

    def dequeue(self):
        if len(self._videoPaths) > 0:
            self._videoPaths.pop(0)
            self._savePaths.pop(0)

    def _openFiles(self):
        videoPaths = selectVideoPaths(native=True)

        for videoPath in reversed(videoPaths):
            self.enqueue(videoPath, [videoPath], first=True)

        self.updateVideo()

    def _openFolders(self):
        directories, (
            recursive,
            sameConfig,
            overwrite,
        ) = selectVideoDirectories(
            (
                ("Include subdirectories", True),
                ("Use one configuration file per directory", True),
                ("Overwrite existing configuration files", True),
            )
        )
        videoPaths, savePaths = get_paths_for_config_creation(
            directories, recursive, sameConfig, overwrite
        )

        for videoPath, savePath in zip(videoPaths, savePaths):
            self.enqueue(videoPath, savePath)

        self.updateVideo()
