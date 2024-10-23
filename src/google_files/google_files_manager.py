import os
from pathlib import Path

import google.generativeai as genai
from dotenv import load_dotenv
from google.api_core.exceptions import PermissionDenied
from google.generativeai.types import File

from exceptions import FileUploadError

from .igoogle_files_mappings import GoogleFilesMappings


class GoogleFilesManager:
    _google_files_data: GoogleFilesMappings
    _max_retries = 2

    def __init__(self, google_files_data: GoogleFilesMappings) -> None:
        load_dotenv()
        assert os.environ.get("API_KEY"), "API_KEY is not set"
        genai.configure(api_key=os.environ["API_KEY"])
        self._google_files_data = google_files_data

    def get_file(self, file_path: str | Path, mime_type: str) -> tuple[File, bool]:
        """
        Retrieves a file from Google using its local file path. If the file is not found,
        it uploads the file to Google and then retrieves it.

        Args:
            file_path (str | Path): The local path of the file to retrieve or upload.
            mime_type (str): The MIME type of the file to be uploaded if it does not exist.
        Returns:
            tuple[File, bool]: A tuple containing the Google File object and a boolean
            indicating whether the file was uploaded (True) or retrieved (False).
        """
        file_name = str(file_path)
        google_file_name = self._google_files_data.get_file(file_name)

        if google_file_name:
            file = GoogleFilesManager._get_google_file_by_uploaded_name(
                google_file_name
            )
            if file:
                return file, False

        file = GoogleFilesManager._upload_google_file_by_file_name(
            file_name, mime_type, self._max_retries
        )
        self.set_file(file_name, file.name)
        return file, True

    def set_file(self, key: str, file_path: str | Path) -> None:
        self._google_files_data.set_file(key, str(file_path))

    @staticmethod
    def _get_google_file_by_uploaded_name(google_file_name: str) -> File | None:
        assert google_file_name.startswith(
            "files/"
        ), f"Invalid file name: {google_file_name}. Must start with 'files/'"
        try:
            file = genai.get_file(name=google_file_name)
            return file
        except PermissionDenied:
            pass

    @staticmethod
    def _upload_google_file_by_file_name(
        file_name: str, mime_type: str, max_retries: int = 2
    ) -> File:
        retries = max_retries
        while retries > 0:
            file = genai.upload_file(file_name, mime_type=mime_type)
            try:
                file = genai.get_file(name=file.name)
                return file
            except PermissionDenied:
                retries -= 1
        raise FileUploadError(f"Could not upload file. Attempts made: {max_retries}")
