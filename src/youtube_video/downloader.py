import json
import re
import subprocess
from enum import Enum
from pathlib import Path


class DownloadStatus(Enum):
    DOWNLOADED = "downloaded"
    EXISTS = "exists"
    ERROR = "error"


class ParsedVideoFormat:
    _regex = re.compile(r"^(\d+).+(\d{3,4})x(\d{3,4}).+")
    _text: str
    _width: int
    _height: int
    _format_id: int

    def __init__(self, text: str) -> None:
        if not ParsedVideoFormat.is_valid(text):
            raise ValueError(f"Invalid video format: {text}")
        self._text = text
        self.parse()

    @classmethod
    def is_valid(cls, text: str) -> bool:
        return "video only" in text

    @property
    def width(self) -> int:
        return self._width

    @property
    def height(self) -> int:
        return self._height

    @property
    def format_id(self) -> int:
        return self._format_id

    def parse(self):
        match = self._regex.match(self._text)
        if match is None:
            raise ValueError(f"Invalid video format: {self._text}")

        self._format_id = int(match.group(1))
        self._width = int(match.group(2))
        self._height = int(match.group(3))


class ParsedAudioFormat:
    _regex = re.compile(r"^(\d+).+(\d{3,4})k https.+")
    _text: str
    _size: int
    _format_id: int

    def __init__(self, text: str) -> None:
        if not ParsedAudioFormat.is_valid(text):
            raise ValueError(f"Invalid audio format: {text}")
        self._text = text
        self.parse()

    @classmethod
    def is_valid(cls, text: str) -> bool:
        return "audio only" in text and cls._regex.match(text) is not None

    @property
    def size(self) -> int:
        return self._size

    @property
    def format_id(self) -> int:
        return self._format_id

    def parse(self):
        match = self._regex.match(self._text)
        if match is None:
            raise ValueError(f"Invalid audio format: {self._text}")

        self._format_id = int(match.group(1))
        self._size = int(match.group(2))


class Downloader:
    _video_id: str
    _output_dir: Path
    _output_file: Path | None = None

    def __init__(self, video_id: str, output_dir: Path) -> None:
        if output_dir.is_file():
            raise ValueError(f"{output_dir} is a file, not a directory")
        output_dir.mkdir(parents=True, exist_ok=True)

        self._video_id = video_id
        self._output_dir = output_dir

    def download(self) -> DownloadStatus:
        if self._is_downloaded():
            return DownloadStatus.EXISTS
        cmd = self._create_cmd()
        print("running cmd", cmd)
        subprocess.run(cmd)
        return (
            DownloadStatus.DOWNLOADED if self._is_downloaded() else DownloadStatus.ERROR
        )

    def _is_downloaded(self):
        return self.downloaded_file() is not None

    def downloaded_file(self) -> Path | None:
        if self._output_file:
            return self._output_file

        for file in self._output_dir.iterdir():
            if (file.stem) == self._video_id:
                self._output_file = self._output_dir / f"{file.name}"
                assert self._output_file.exists(), "Error setting output file"
                return self._output_file

        return None

    def _create_cmd(self) -> str:
        download_command = DownloadCommand(self._video_id, self._output_dir)
        return download_command.create()


class DownloadCommand:
    MAX_DURATION = 45 * 60  # Max duration for the Vertex API
    OPTIMAL_VIDEO_HEIGHT_BREAKPOINT = 1000
    _video_id: str
    _output_dir: Path

    def __init__(self, video_id: str, output_dir: str | Path) -> None:
        self._video_id = video_id
        self._output_dir = Path(output_dir)

    @property
    def _output_arg(self) -> Path:
        return self._output_dir / f"{self._video_id}"

    @property
    def _url(self) -> str:
        return f"https://youtu.be/{self._video_id}"

    def create(self) -> str:
        video_format, audio_format = self._get_best_formats()
        return f'yt-dlp -q -4 -f {video_format.format_id}+{audio_format.format_id} {self._url} -o "{str(self._output_arg)}"'

    def _get_available_formats(
        self,
    ) -> tuple[list[ParsedVideoFormat], list[ParsedAudioFormat]]:
        raw_output = self._get_formats_raw_output()
        parsed_video_formats: list[ParsedVideoFormat] = []
        parsed_audio_formats: list[ParsedAudioFormat] = []
        for line in raw_output.splitlines():
            if ParsedVideoFormat.is_valid(line):
                parsed_video_formats.append(ParsedVideoFormat(line))
            if ParsedAudioFormat.is_valid(line):
                parsed_audio_formats.append(ParsedAudioFormat(line))

        return parsed_video_formats, parsed_audio_formats

    def _get_best_formats(self) -> tuple[ParsedVideoFormat, ParsedAudioFormat]:
        video_formats, audio_formats = self._get_available_formats()
        sorted_video_formats = sorted(video_formats, key=lambda x: x.height)
        sorted_audio_formats = sorted(audio_formats, key=lambda x: x.size)

        assert len(sorted_video_formats) > 0, f"No valid formats found: {video_formats}"
        assert len(sorted_audio_formats) > 0, (
            f"No valid audio formats found: {audio_formats}"
        )

        best_video_format = sorted_video_formats[0]
        best_audio_format = sorted_audio_formats[0]

        for format in sorted_video_formats:
            if format.height > best_video_format.height:
                best_video_format = format
            if format.height > DownloadCommand.OPTIMAL_VIDEO_HEIGHT_BREAKPOINT:
                break

        for format in sorted_audio_formats:
            if format.size > best_audio_format.size:
                best_audio_format = format

        return best_video_format, best_audio_format

    def _get_formats_raw_output(self) -> str:
        import shlex

        cmd = f"yt-dlp -F {self._url}"
        process = subprocess.run(
            shlex.split(cmd), capture_output=True, text=True, check=True
        )
        return process.stdout

    def _get_duration_in_seconds(self) -> int:
        import shlex

        cmd = f"yt-dlp -J --skip-download {self._url}"
        data = json.loads(
            subprocess.run(
                shlex.split(cmd),
                capture_output=True,
                text=True,
                check=True,
            ).stdout.strip()
        )
        try:
            assert "duration" in data, "Error getting duration. Not found"
            assert isinstance(data["duration"], int), (
                "Error getting duration. Not a number"
            )
        except AssertionError as e:
            print("Dumping data in errordump.json")
            with open("errordump.json", "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            raise e

        return int(data["duration"])
