import unittest
from typing import cast

from google import genai
from google.genai import errors, types

from exceptions import FileUploadError
from google_files import GoogleFilesManager


def api_error(code):
    return errors.ClientError(code, {"error": {"code": code, "message": "nope"}})


class MemoryMappings:
    def __init__(self, entries=None):
        self.entries = dict(entries or {})

    def get_file(self, local_file_path):
        return self.entries.get(local_file_path)

    def set_file(self, local_file_path, google_file_name):
        self.entries[local_file_path] = google_file_name


class FakeFiles:
    """Stands in for `client.files`, answering `get` from a scripted queue."""

    def __init__(self, get_results=(), upload_names=()):
        self.get_results = list(get_results)
        self.upload_names = list(upload_names)
        self.gets = []
        self.uploads = []

    def get(self, *, name):
        self.gets.append(name)
        result = self.get_results.pop(0)
        if isinstance(result, Exception):
            raise result
        return types.File(name=name, state=result)

    def upload(self, *, file, config):
        self.uploads.append((file, config.mime_type))
        return types.File(
            name=self.upload_names.pop(0), state=types.FileState.PROCESSING
        )


class FakeClient:
    def __init__(self, files):
        self.files = files


def manager(mappings, files):
    return GoogleFilesManager(mappings, cast(genai.Client, FakeClient(files)))


class GoogleFilesManagerTests(unittest.TestCase):
    def test_cached_upload_is_reused(self):
        files = FakeFiles(get_results=[types.FileState.ACTIVE])
        mappings = MemoryMappings({"video.mp4": "files/abc"})

        file, uploaded = manager(mappings, files).get_file(
            "video.mp4", "video/mp4"
        )

        self.assertFalse(uploaded)
        self.assertEqual(file.name, "files/abc")
        self.assertEqual(files.gets, ["files/abc"])
        self.assertEqual(files.uploads, [])

    def test_expired_cached_upload_is_replaced(self):
        files = FakeFiles(
            get_results=[api_error(403), types.FileState.PROCESSING],
            upload_names=["files/new"],
        )
        mappings = MemoryMappings({"video.mp4": "files/old"})

        file, uploaded = manager(mappings, files).get_file(
            "video.mp4", "video/webm"
        )

        self.assertTrue(uploaded)
        self.assertEqual(file.name, "files/new")
        self.assertEqual(files.uploads, [("video.mp4", "video/webm")])
        self.assertEqual(mappings.entries["video.mp4"], "files/new")

    def test_unknown_cached_upload_is_replaced(self):
        files = FakeFiles(
            get_results=[api_error(404), types.FileState.ACTIVE],
            upload_names=["files/new"],
        )
        mappings = MemoryMappings({"video.mp4": "files/gone"})

        _, uploaded = manager(mappings, files).get_file(
            "video.mp4", "video/mp4"
        )

        self.assertTrue(uploaded)
        self.assertEqual(mappings.entries["video.mp4"], "files/new")

    def test_uncached_video_is_uploaded_and_recorded(self):
        files = FakeFiles(
            get_results=[types.FileState.PROCESSING], upload_names=["files/xyz"]
        )
        mappings = MemoryMappings()

        file, uploaded = manager(mappings, files).get_file(
            "video.mp4", "video/mp4"
        )

        self.assertTrue(uploaded)
        self.assertEqual(file.state, types.FileState.PROCESSING)
        self.assertEqual(mappings.entries, {"video.mp4": "files/xyz"})

    def test_upload_retries_then_gives_up(self):
        files = FakeFiles(
            get_results=[api_error(403), api_error(403)],
            upload_names=["files/a", "files/b"],
        )
        mappings = MemoryMappings()

        with self.assertRaises(FileUploadError):
            manager(mappings, files).get_file(
                "video.mp4", "video/mp4"
            )

        self.assertEqual(len(files.uploads), 2)
        self.assertEqual(mappings.entries, {})

    def test_other_api_errors_are_not_swallowed(self):
        files = FakeFiles(get_results=[api_error(429)])
        mappings = MemoryMappings({"video.mp4": "files/abc"})

        with self.assertRaises(errors.ClientError):
            manager(mappings, files).get_file(
                "video.mp4", "video/mp4"
            )


if __name__ == "__main__":
    unittest.main()
