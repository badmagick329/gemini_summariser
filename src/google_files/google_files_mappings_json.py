import json
from pathlib import Path


class GoogleFilesMappingsJson:
    _data: dict[str, dict[str, str | int]]
    _save_file: Path

    def __init__(self, json_file: Path) -> None:
        if json_file.exists():
            assert json_file.is_file(), f"{json_file} is not a file"
            self._save_file = json_file
            self._load()
        else:
            json_file.parent.mkdir(parents=True, exist_ok=True)
            self._save_file = json_file
            self._data = {}
            self._save()

    def _save(self) -> None:
        with open(self._save_file, "w") as f:
            f.write(json.dumps(self._data))

    def _load(self) -> None:
        with open(self._save_file, "r") as f:
            self._data = json.loads(f.read())

    def get_file(self, local_file_path: str) -> str | None:
        """Reuse an upload only while the source file still matches its saved version."""
        record = self._data.get(local_file_path)
        if not isinstance(record, dict):
            return None
        stat = Path(local_file_path).stat()
        if (
            record.get("size") != stat.st_size
            or record.get("mtime_ns") != stat.st_mtime_ns
        ):
            return None
        name = record.get("name")
        return name if isinstance(name, str) else None

    def set_file(self, local_file_path: str, google_file_name: str) -> None:
        stat = Path(local_file_path).stat()
        self._data[local_file_path] = {
            "name": google_file_name,
            "size": stat.st_size,
            "mtime_ns": stat.st_mtime_ns,
        }
        self._save()
