from pathlib import Path

from downloader import Downloader, DownloadStatus

from .base_video import BaseVideo


class YoutubeVideo(BaseVideo):
    _youtube_url: str
    _output_dir: Path
    _video_id: str
    _output_file: Path | None = None
    _downloader: Downloader

    def __init__(self, url: str, output_dir: Path) -> None:
        if "youtube.com/watch?v" in url:
            self._video_id = url.split("&")[0].split("?v=")[-1]
        elif "youtu.be/" in url:
            self._video_id = url.split("?")[0].split("youtu.be/")[-1]
        else:
            raise ValueError(f"Invalid youtube url: {url}")

        self._downloader = Downloader(self.video_id, output_dir)

        self._youtube_url = url
        self._output_dir = output_dir

    def download(self) -> DownloadStatus:
        return self._downloader.download()

    @property
    def path(self) -> Path:
        downloaded_file = self._downloader.downloaded_file()
        if downloaded_file is None:
            raise ValueError("File not downloaded")
        return downloaded_file

    @staticmethod
    def is_youtube_url(url: str) -> bool:
        return "youtube.com/watch?v" in url or "youtu.be/" in url

    @property
    def video_id(self) -> str:
        return self._video_id
