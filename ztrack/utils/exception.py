class TrackingError(Exception):
    pass


class VideoTrackingError(Exception):
    def __init__(self, frame: int):
        self.frame = frame
