import importlib.util
import json
import os
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

from .download_status import DownloadStatus
from .parsed_audio_format import ParsedAudioFormat
from .parsed_video_format import ParsedVideoFormat


class Downloader:
    _video_id: str
    _output_dir: Path
    _output_file: Path | None = None

    def __init__(self, video_id: str, output_dir: str | Path) -> None:
        output_dir = Path(output_dir)
        if output_dir.is_file():
            raise ValueError(f"{output_dir} is a file, not a directory")
        output_dir.mkdir(parents=True, exist_ok=True)

        self._video_id = video_id
        self._output_dir = output_dir

    def download(self) -> DownloadStatus:
        if self._is_downloaded():
            return DownloadStatus.EXISTS
        known_files = set(self._video_files())
        try:
            cmd = self._create_cmd()
        except (FileNotFoundError, ValueError, subprocess.CalledProcessError) as error:
            print(f"Could not prepare yt-dlp download: {error}")
            return DownloadStatus.ERROR
        print("Downloading YouTube video...")
        try:
            subprocess.run(cmd, check=True)
        except subprocess.CalledProcessError as error:
            print(f"yt-dlp failed: {error}")
            return DownloadStatus.ERROR
        except OSError as error:
            print(f"Could not start yt-dlp: {error}")
            return DownloadStatus.ERROR
        self._output_file = self._new_downloaded_file(known_files)
        if self._output_file:
            self._save_downloaded_file(self._output_file)
        return (
            DownloadStatus.DOWNLOADED if self._is_downloaded() else DownloadStatus.ERROR
        )

    def _is_downloaded(self):
        return self.downloaded_file() is not None

    def downloaded_file(self) -> Path | None:
        if self._output_file:
            return self._output_file

        manifest_file = self._output_dir / ".downloads.json"
        if manifest_file.exists():
            try:
                saved_path = json.loads(manifest_file.read_text(encoding="utf-8")).get(
                    self._video_id
                )
                if saved_path and Path(saved_path).is_file():
                    self._output_file = Path(saved_path)
                    return self._output_file
            except (json.JSONDecodeError, OSError):
                pass

        for file in self._output_dir.iterdir():
            if (file.stem) == self._video_id:
                self._output_file = self._output_dir / f"{file.name}"
                assert self._output_file.exists(), "Error setting output file"
                return self._output_file

        return None

    def _video_files(self) -> list[Path]:
        return [file for file in self._output_dir.iterdir() if file.is_file()]

    def _new_downloaded_file(self, known_files: set[Path]) -> Path | None:
        new_files = [file for file in self._video_files() if file not in known_files]
        if not new_files:
            return None
        return max(new_files, key=lambda file: file.stat().st_mtime).resolve()

    def _save_downloaded_file(self, path: Path) -> None:
        manifest_file = self._output_dir / ".downloads.json"
        try:
            downloads = json.loads(manifest_file.read_text(encoding="utf-8"))
        except (FileNotFoundError, json.JSONDecodeError):
            downloads = {}
        downloads[self._video_id] = str(path)
        manifest_file.write_text(json.dumps(downloads, indent=2), encoding="utf-8")

    def _create_cmd(self) -> list[str]:
        download_command = DownloadCommand(self._video_id, self._output_dir)
        return download_command.create()


@dataclass(frozen=True)
class YoutubeDownloadSettings:
    """yt-dlp settings controlled by optional environment variables.

    YTDLP_EXECUTABLE must name a native executable, not a shell alias or .bat shim.
    YTDLP_EXTRA_ARGS is a JSON array, avoiding shell-specific quoting and escaping.
    """

    command_prefix: tuple[str, ...]
    format_selector: str | None
    cookies_file: str | None
    js_runtimes: str | None
    config_location: str | None
    output_template: str
    extra_args: tuple[str, ...]

    @classmethod
    def from_environment(cls) -> "YoutubeDownloadSettings":
        configured_executable = os.getenv("YTDLP_EXECUTABLE")
        command_prefix = (
            (configured_executable,)
            if configured_executable
            else cls._find_command_prefix()
        )

        extra_args_raw = os.getenv("YTDLP_EXTRA_ARGS", "[]")
        try:
            extra_args = json.loads(extra_args_raw)
        except json.JSONDecodeError as error:
            raise ValueError("YTDLP_EXTRA_ARGS must be a JSON array of strings.") from error
        if not isinstance(extra_args, list) or not all(
            isinstance(arg, str) for arg in extra_args
        ):
            raise ValueError("YTDLP_EXTRA_ARGS must be a JSON array of strings.")

        return cls(
            command_prefix=command_prefix,
            format_selector=os.getenv("YTDLP_FORMAT") or None,
            cookies_file=os.getenv("YTDLP_COOKIES_FILE") or None,
            js_runtimes=os.getenv("YTDLP_JS_RUNTIMES") or None,
            config_location=os.getenv("YTDLP_CONFIG_LOCATION") or None,
            output_template=os.getenv("YTDLP_OUTPUT_TEMPLATE", "%(id)s.%(ext)s"),
            extra_args=tuple(extra_args),
        )

    @staticmethod
    def _find_command_prefix() -> tuple[str, ...]:
        """Find a direct executable first, then use the current Python module."""
        executable = shutil.which("yt-dlp.exe") or shutil.which("yt-dlp")
        if executable and not (
            os.name == "nt" and Path(executable).suffix.lower() in {".bat", ".cmd"}
        ):
            return (executable,)

        if importlib.util.find_spec("yt_dlp"):
            return (sys.executable, "-m", "yt_dlp")

        raise FileNotFoundError(
            "yt-dlp was not found. Install yt-dlp on PATH, install it in this Python "
            "environment, or set YTDLP_EXECUTABLE to a native yt-dlp executable."
        )


class DownloadCommand:
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

    def create(self) -> list[str]:
        settings = YoutubeDownloadSettings.from_environment()
        format_selector = settings.format_selector or self._get_best_format_selector(
            settings
        )
        command = [
            *settings.command_prefix,
            "--no-playlist",
            "--format",
            format_selector,
            "--output",
            str(self._output_dir / settings.output_template),
        ]
        if settings.cookies_file:
            command.extend(["--cookies", settings.cookies_file])
        if settings.js_runtimes:
            command.extend(["--js-runtimes", settings.js_runtimes])
        if settings.config_location:
            command.extend(["--config-locations", settings.config_location])
        command.extend(settings.extra_args)
        command.append(self._url)
        return command

    def _get_best_format_selector(self, settings: YoutubeDownloadSettings) -> str:
        video_formats, audio_formats = self._get_available_formats(settings)
        sorted_video_formats = sorted(video_formats, key=lambda format: format.height)
        sorted_audio_formats = sorted(audio_formats, key=lambda format: format.size)
        if not sorted_video_formats:
            raise ValueError("yt-dlp did not return any usable video-only formats.")
        if not sorted_audio_formats:
            raise ValueError("yt-dlp did not return any usable audio-only formats.")

        best_video_format = sorted_video_formats[0]
        for video_format in sorted_video_formats:
            if video_format.height > best_video_format.height:
                best_video_format = video_format
            if video_format.height > self.OPTIMAL_VIDEO_HEIGHT_BREAKPOINT:
                break

        best_audio_format = sorted_audio_formats[-1]
        return f"{best_video_format.format_id}+{best_audio_format.format_id}"

    def _get_available_formats(
        self, settings: YoutubeDownloadSettings
    ) -> tuple[list[ParsedVideoFormat], list[ParsedAudioFormat]]:
        command = [*settings.command_prefix, "--no-playlist"]
        if settings.cookies_file:
            command.extend(["--cookies", settings.cookies_file])
        if settings.js_runtimes:
            command.extend(["--js-runtimes", settings.js_runtimes])
        if settings.config_location:
            command.extend(["--config-locations", settings.config_location])
        command.extend(["--list-formats", self._url])
        process = subprocess.run(command, capture_output=True, text=True, check=True)

        video_formats = [
            ParsedVideoFormat(line)
            for line in process.stdout.splitlines()
            if ParsedVideoFormat.is_valid(line)
        ]
        audio_formats = [
            ParsedAudioFormat(line)
            for line in process.stdout.splitlines()
            if ParsedAudioFormat.is_valid(line)
        ]
        return video_formats, ParsedAudioFormat.remove_alternative_languages(audio_formats)
