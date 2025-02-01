import subprocess
from enum import Enum
from pathlib import Path


class DownloadStatus(Enum):
    DOWNLOADED = "downloaded"
    EXISTS = "exists"
    ERROR = "error"


class Video:
    _youtube_url: str
    _output_dir: Path
    _video_id: str
    _output_file: Path | None = None

    def __init__(self, youtube_url: str, output_dir: Path) -> None:
        if output_dir.is_file():
            raise ValueError(f"{output_dir} is a file, not a directory")
        output_dir.mkdir(parents=True, exist_ok=True)

        if "youtube.com/watch?v" in youtube_url:
            self._video_id = youtube_url.split("&")[0].split("?v=")[-1]
        elif "youtu.be/" in youtube_url:
            self._video_id = youtube_url.split("?")[0].split("youtu.be/")[-1]
        else:
            raise ValueError(f"Invalid youtube url: {youtube_url}")

        self._youtube_url = youtube_url
        self._output_dir = output_dir

    def is_downloaded(self):
        return self.downloaded_file() is not None

    def download(self) -> DownloadStatus:
        if self.is_downloaded():
            return DownloadStatus.EXISTS
        cmd = self._create_cmd()
        print("running cmd", cmd)
        subprocess.run(cmd)
        return (
            DownloadStatus.DOWNLOADED if self.is_downloaded() else DownloadStatus.ERROR
        )

    @property
    def output_file_without_ext(self) -> Path:
        return self._output_dir / f"{self.video_id}"

    def downloaded_file(self) -> Path | None:
        if self._output_file:
            return self._output_file

        for file in self._output_dir.iterdir():
            if (file.stem) == self._video_id:
                self._output_file = self._output_dir / f"{file.name}"
                assert self._output_file.exists(), "Error setting output file"
                return self._output_file

        return None

    @property
    def video_id(self) -> str:
        return self._video_id

    def _create_cmd(self) -> str:
        return (
            f"yt-dlp -q -4 https://youtu.be/{self.video_id} "
            f'-o "{str(self.output_file_without_ext)}"'
        )
