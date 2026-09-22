import json
import tempfile
import unittest
from pathlib import Path

from google_files import GoogleFilesMappingsJson


class GoogleFilesMappingsTests(unittest.TestCase):
    def test_replaced_file_does_not_reuse_old_upload(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            video = root / "clip.mp4"
            video.write_bytes(b"original")
            mappings = GoogleFilesMappingsJson(root / "mappings.json")
            mappings.set_file(str(video), "files/original")

            self.assertEqual(mappings.get_file(str(video)), "files/original")

            video.write_bytes(b"replacement with a different size")

            self.assertIsNone(mappings.get_file(str(video)))
            mappings.set_file(str(video), "files/replacement")
            self.assertEqual(mappings.get_file(str(video)), "files/replacement")

    def test_old_path_only_mapping_requires_a_new_upload(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            video = root / "clip.mp4"
            video.write_bytes(b"video")
            mapping_path = root / "mappings.json"
            mapping_path.write_text(
                json.dumps({str(video): "files/old"}), encoding="utf-8"
            )

            self.assertIsNone(
                GoogleFilesMappingsJson(mapping_path).get_file(str(video))
            )
