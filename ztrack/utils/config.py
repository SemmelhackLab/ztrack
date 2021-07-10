from configparser import ConfigParser
from pathlib import Path


config = ConfigParser()
config.read(Path(__file__).parent.parent.parent.joinpath("config.ini"))

video_extensions = tuple(
    config.get("extensions", "VideoExtensions").split(" ")
)
config_extension = config.get("extensions", "ConfigExtension")
