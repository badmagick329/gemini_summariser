import json
import os
import tempfile
import unittest
from datetime import datetime, timedelta
from pathlib import Path

from cleanup import CleanupManager


class CleanupManagerTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        root = Path(self.temp_dir.name)
        self.videos = root / "videos"
        self.outputs = root / "outputs"
        self.videos.mkdir()
        self.outputs.mkdir()
        self.manifest = self.videos / ".downloads.json"
        self.mappings = root / "google_files_mappings.json"
        self.manager = CleanupManager(self.videos, self.outputs, self.manifest, self.mappings)

    def tearDown(self):
        self.temp_dir.cleanup()

    def make_old(self, path: Path, days: int) -> Path:
        path.write_bytes(b"x" * 100)
        old_time = (datetime.now() - timedelta(days=days)).timestamp()
        os.utime(path, (old_time, old_time))
        return path

    def test_preview_does_not_change_files_or_mappings(self):
        old_video = self.make_old(self.videos / "old.mp4", 8)
        self.manifest.write_text(json.dumps({"old": str(old_video)}), encoding="utf-8")
        self.mappings.write_text(json.dumps({str(old_video): "files/old"}), encoding="utf-8")

        plan = self.manager.plan(days=7, part_days=1, include_outputs=False)

        self.assertEqual(plan.files, (old_video,))
        self.assertTrue(old_video.exists())
        self.assertEqual(json.loads(self.manifest.read_text()), {"old": str(old_video)})

    def test_apply_removes_old_managed_files_and_their_mappings(self):
        old_video = self.make_old(self.videos / "old.mp4", 8)
        old_part = self.make_old(self.videos / "failed.mp4.part", 2)
        old_summary = self.make_old(self.outputs / "old.md", 8)
        outside_file = self.make_old(Path(self.temp_dir.name) / "user-video.mp4", 8)
        self.manifest.write_text(json.dumps({"old": str(old_video)}), encoding="utf-8")
        self.mappings.write_text(
            json.dumps({str(old_video): "files/old", str(outside_file): "files/user"}),
            encoding="utf-8",
        )

        plan = self.manager.plan(days=7, part_days=1, include_outputs=True)
        self.manager.apply(plan)

        self.assertFalse(old_video.exists())
        self.assertFalse(old_part.exists())
        self.assertFalse(old_summary.exists())
        self.assertTrue(outside_file.exists())
        self.assertEqual(json.loads(self.manifest.read_text()), {})
        self.assertEqual(
            json.loads(self.mappings.read_text()), {str(outside_file): "files/user"}
        )
