from pathlib import Path

from .base_video import BaseVideo
from .youtube_video import YoutubeVideo


class VideoFactory:
    _output_dir: Path

    def __init__(self, output_dir: Path) -> None:
        self._output_dir = output_dir

    def create_video(self, input: str) -> BaseVideo:
        youtube_video = YoutubeVideo(input, self._output_dir)

        print("Downloding youtube video...")
        download_status = youtube_video.download()
        if download_status == "ERROR":
            raise ValueError(f"Error downloading video: {input}")
        print(download_status)
        print(youtube_video.path())
        if youtube_video.path() is None:
            raise ValueError("Error downloading file")

        return youtube_video
