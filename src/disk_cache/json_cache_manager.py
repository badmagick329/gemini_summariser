import hashlib
import json
from pathlib import Path


class FileRemovalError(Exception):
    pass


class JsonCacheManager:
    _cache_dir: Path
    _save_file: Path
    _cache: dict[str, str]

    def __init__(self, cache_dir: Path, save_file_name: str) -> None:
        self._cache_dir = cache_dir
        self._save_file = self._cache_dir / save_file_name

        if self._save_file.exists():
            assert self._save_file.is_file(), f"{self._save_file} is not a file"
            self._load()
        else:
            self._save_file.parent.mkdir(parents=True, exist_ok=True)
            self._cache = {}
            self._save()

    def _save(self):
        with open(self._save_file, "w") as f:
            f.write(json.dumps(self._cache))

    def _load(self):
        with open(self._save_file, "r") as f:
            self._cache = json.loads(f.read())

    def get_for(self, key: str) -> Path | None:
        cached_data_file = self._cache.get(key)
        return self._cache_dir / cached_data_file if cached_data_file else None

    def set_for(self, key: str) -> None:
        path = str(self._cache_dir / self._hash(key))
        self._cache[key] = path
        self._save()

    def del_key(self, key: str) -> None:
        saved_value = self._cache.get(key)
        if saved_value is None:
            return None

        try:
            Path(saved_value).unlink()
        except (FileNotFoundError, IsADirectoryError, OSError, PermissionError) as e:
            raise FileRemovalError(f"Could not remove file {saved_value}\n{e}")

        del self._cache[key]
        self._save()

    def _hash(self, string: str) -> str:
        hasher = hashlib.new("256")
        hasher.update(string.encode())
        return hasher.hexdigest()
