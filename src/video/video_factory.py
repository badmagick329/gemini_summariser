from pathlib import Path

from downloader import DownloadStatus

from .base_video import BaseVideo
from .local_video import LocalVideo
from .youtube_video import YoutubeVideo


class VideoFactory:
    _output_dir: Path

    def __init__(self, output_dir: Path) -> None:
        self._output_dir = output_dir

    def create_video(self, input: str) -> BaseVideo:
        if YoutubeVideo.is_youtube_url(input):
            youtube_video = YoutubeVideo(input, self._output_dir)

            print("Downloding youtube video...")
            download_status = youtube_video.download()
            if download_status == DownloadStatus.ERROR:
                raise ValueError(f"Error downloading video: {input}")
            print(download_status)
            print(youtube_video.path)

            return youtube_video

        path = Path(input)
        if path.is_file():
            return LocalVideo(path)

        raise ValueError(f"Input is not a local file or a youtube video: {input}")
