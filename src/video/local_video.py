from pathlib import Path

from .base_video import BaseVideo


class LocalVideo(BaseVideo):
    _path: Path

    def __init__(self, path: Path):
        assert path.is_file()
        self._path = path.absolute().resolve()

    @property
    def path(self) -> Path:
        return self._path

    @property
    def video_id(self) -> str:
        return str(self._path)
