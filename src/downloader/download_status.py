from enum import Enum


class DownloadStatus(Enum):
    DOWNLOADED = "downloaded"
    EXISTS = "exists"
    ERROR = "error"
