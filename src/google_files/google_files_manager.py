from pathlib import Path

from google import genai
from google.genai import errors, types

from exceptions import FileUploadError

from .igoogle_files_mappings import GoogleFilesMappings

# The File API answers 403 for files that expired (48h) or belong to another
# key, and 404 for names it has never seen. Either way the cached upload is
# unusable and the video has to be uploaded again.
_UNUSABLE_FILE_CODES = (403, 404)


class GoogleFilesManager:
    _google_files_data: GoogleFilesMappings
    _client: genai.Client
    _max_retries = 2

    def __init__(
        self, google_files_data: GoogleFilesMappings, client: genai.Client
    ) -> None:
        self._google_files_data = google_files_data
        self._client = client

    def get_file(
        self, file_path: str | Path, mime_type: str
    ) -> tuple[types.File, bool]:
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
            file = self._get_google_file_by_uploaded_name(google_file_name)
            if file:
                return file, False

        file = self._upload_google_file_by_file_name(file_name, mime_type)
        self.set_file(file_name, self._file_name(file))
        return file, True

    def set_file(self, key: str, file_path: str | Path) -> None:
        self._google_files_data.set_file(key, str(file_path))

    def _get_google_file_by_uploaded_name(
        self, google_file_name: str
    ) -> types.File | None:
        assert google_file_name.startswith(
            "files/"
        ), f"Invalid file name: {google_file_name}. Must start with 'files/'"
        try:
            return self._client.files.get(name=google_file_name)
        except errors.ClientError as error:
            if error.code in _UNUSABLE_FILE_CODES:
                return None
            raise

    def _upload_google_file_by_file_name(
        self, file_name: str, mime_type: str
    ) -> types.File:
        retries = self._max_retries
        while retries > 0:
            uploaded = self._client.files.upload(
                file=file_name, config=types.UploadFileConfig(mime_type=mime_type)
            )
            # A fresh upload is occasionally not yet readable; re-fetching proves
            # the name is usable before it goes into the upload cache.
            try:
                return self._client.files.get(name=self._file_name(uploaded))
            except errors.ClientError as error:
                if error.code not in _UNUSABLE_FILE_CODES:
                    raise
                retries -= 1
        raise FileUploadError(
            f"Could not upload file. Attempts made: {self._max_retries}"
        )

    @staticmethod
    def _file_name(file: types.File) -> str:
        # The File API always names stored files; a nameless one means the
        # response is not what the upload cache can reference later.
        if not file.name:
            raise FileUploadError("Gemini returned an uploaded file without a name")
        return file.name
