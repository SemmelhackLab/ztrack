from pathlib import Path

import cv2
import numpy as np
from decord import VideoReader


class MyVideoReader(VideoReader):
    def __init__(self, path, bg_frames=0, dark_fish=-1):
        super().__init__(Path(path).as_posix())

        self.bg = None
        self.dark_fish = dark_fish

        if bg_frames:
            bg_frames = min(len(self), bg_frames)
            idx = np.round(np.linspace(0, len(self) - 1, bg_frames)).astype(int)
            self.bg = np.median([self._getitem(i) for i in idx], axis=0).astype(np.uint8)

            if dark_fish < 0:
                self.dark_fish = self.bg.mean() > 128

        if dark_fish == -1:
            self.dark_fish = self._getitem(0).mean() > 128
        else:
            self.dark_fish = dark_fish

    def _getitem(self, idx):
        im = super(MyVideoReader, self).__getitem__(idx).asnumpy()
        if im.ndim == 3:
            return cv2.cvtColor(im, cv2.COLOR_RGB2GRAY)
        return im

    def __getitem__(self, idx):
        frame = self._getitem(idx)

        if self.bg is not None:
            if self.dark_fish:
                return cv2.subtract(self.bg, frame)
            else:
                return cv2.subtract(frame, self.bg)
        else:
            return ~frame if self.dark_fish else frame
