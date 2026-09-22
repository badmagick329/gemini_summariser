import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from downloader.downloader import DownloadCommand, Downloader, YoutubeDownloadSettings


class DownloadCommandTests(unittest.TestCase):
    def test_uses_individual_arguments_and_youtube_settings(self):
        with patch.dict(
            os.environ,
            {
                "YTDLP_EXECUTABLE": r"C:\\tools\\yt-dlp.exe",
                "YTDLP_COOKIES_FILE": r"C:\\cookies.txt",
                "YTDLP_JS_RUNTIMES": "deno",
                "YTDLP_FORMAT": "137+140",
                "YTDLP_OUTPUT_TEMPLATE": "%(upload_date>%y%m%d)s %(title)s.%(ext)s",
                "YTDLP_EXTRA_ARGS": '["--sleep-requests", "1"]',
            },
            clear=True,
        ):
            command = DownloadCommand("video-id", Path("downloads")).create()

        self.assertEqual(command[0], r"C:\\tools\\yt-dlp.exe")
        self.assertIn("--cookies", command)
        self.assertIn(r"C:\\cookies.txt", command)
        self.assertIn("--js-runtimes", command)
        self.assertIn("deno", command)
        self.assertNotIn("--print", command)
        self.assertTrue(
            command[command.index("--output") + 1].endswith(
                "%(upload_date>%y%m%d)s %(title)s.%(ext)s"
            )
        )
        self.assertEqual(command[-1], "https://youtu.be/video-id")

    def test_custom_template_path_is_reused_via_manifest(self):
        with tempfile.TemporaryDirectory() as directory:
            download_dir = Path(directory)
            saved_file = download_dir / "240101 Example video.mp4"
            saved_file.touch()

            downloader = Downloader("video-id", download_dir)
            downloader._save_downloaded_file(saved_file)

            self.assertEqual(
                Downloader("video-id", download_dir).downloaded_file(), saved_file
            )

    def test_partial_download_is_not_reused_as_completed_video(self):
        with tempfile.TemporaryDirectory() as directory:
            download_dir = Path(directory)
            partial = download_dir / "video-id.part"
            partial.touch()
            downloader = Downloader("video-id", download_dir)

            self.assertIsNone(downloader.downloaded_file())
            self.assertIsNone(downloader._new_downloaded_file(set()))

            downloader._save_downloaded_file(partial)
            self.assertIsNone(Downloader("video-id", download_dir).downloaded_file())

    def test_falls_back_to_the_current_python_module(self):
        with (
            patch.dict(os.environ, {}, clear=True),
            patch("downloader.downloader.shutil.which", return_value=None),
            patch("downloader.downloader.importlib.util.find_spec", return_value=object()),
        ):
            settings = YoutubeDownloadSettings.from_environment()

        self.assertEqual(settings.command_prefix[1:], ("-m", "yt_dlp"))


if __name__ == "__main__":
    unittest.main()
