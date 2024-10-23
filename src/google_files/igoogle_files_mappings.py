from typing import Protocol


class GoogleFilesMappings(Protocol):
    """
    Map local file path names to their google path name equivalents with persistant storage
    """

    def get_file(self, local_file_path: str) -> str | None: ...

    def set_file(self, local_file_path: str, google_file_name: str) -> None: ...
