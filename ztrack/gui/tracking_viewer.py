from pathlib import Path
from typing import List

from PyQt5 import QtGui, QtWidgets

from ztrack.gui.utils.file import selectVideoDirectories, selectVideoPaths
from ztrack.utils.file import get_paths_for_view_results, video_extensions
from ._main_window import MainWindow


class TrackingViewer(MainWindow):
    def __init__(
        self,
        parent: QtWidgets.QWidget = None,
        videoPaths: List[str] = None,
        verbose=False,
    ):
        super().__init__(parent, videoPaths=videoPaths, verbose=verbose)
        self.updateVideo()

    def dropEvent(self, event: QtGui.QDropEvent) -> None:
        paths = [u.toLocalFile() for u in event.mimeData().urls()]
        for path in paths:
            self.enqueue(path, first=True)
        self.updateVideo()

    def _onFrameChanged(self):
        img = self._currentFrame
        if img is not None:
            self._trackingImageView.setImage(img)

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
            (
                ("Include subdirectories", True),
            )
        )
        videoPaths = get_paths_for_view_results(
            directories,
            recursive,
        )
        for videoPath in videoPaths:
            self.enqueue(videoPath)
        self.updateVideo()
