import json
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path


@dataclass(frozen=True)
class CleanupPlan:
    files: tuple[Path, ...]
    stale_download_ids: tuple[str, ...]
    stale_google_mapping_keys: tuple[str, ...]

    @property
    def bytes_to_reclaim(self) -> int:
        return sum(path.stat().st_size for path in self.files if path.exists())


class CleanupManager:
    """Plan and apply cleanup only within the app-managed data directory."""

    def __init__(
        self,
        videos_dir: Path,
        outputs_dir: Path,
        downloads_manifest: Path,
        google_files_mapping: Path,
    ) -> None:
        self._videos_dir = videos_dir.resolve()
        self._outputs_dir = outputs_dir.resolve()
        self._downloads_manifest = downloads_manifest
        self._google_files_mapping = google_files_mapping

    def plan(self, days: int, part_days: int, include_outputs: bool) -> CleanupPlan:
        now = datetime.now()
        files = self._files_older_than(
            self._videos_dir, now - timedelta(days=days), exclude_hidden=True
        )
        files.extend(
            self._files_older_than(
                self._videos_dir, now - timedelta(days=part_days), suffix=".part"
            )
        )
        if include_outputs:
            files.extend(self._files_older_than(self._outputs_dir, now - timedelta(days=days)))

        unique_files = tuple(dict.fromkeys(files))
        deleted_video_paths = {path.resolve() for path in unique_files if self._is_video(path)}
        stale_download_ids = tuple(
            video_id
            for video_id, file_path in self._read_json(self._downloads_manifest).items()
            if self._is_managed_video_path(Path(file_path))
            and (not Path(file_path).is_file() or Path(file_path).resolve() in deleted_video_paths)
        )
        stale_google_mapping_keys = tuple(
            local_path
            for local_path in self._read_json(self._google_files_mapping).keys()
            if self._is_managed_video_path(Path(local_path))
            and (not Path(local_path).is_file() or Path(local_path).resolve() in deleted_video_paths)
        )
        return CleanupPlan(unique_files, stale_download_ids, stale_google_mapping_keys)

    def apply(self, plan: CleanupPlan) -> None:
        for path in plan.files:
            if path.exists():
                path.unlink()

        self._remove_json_keys(self._downloads_manifest, plan.stale_download_ids)
        self._remove_json_keys(self._google_files_mapping, plan.stale_google_mapping_keys)

    def _files_older_than(
        self,
        directory: Path,
        cutoff: datetime,
        suffix: str | None = None,
        exclude_hidden: bool = False,
    ) -> list[Path]:
        if not directory.exists():
            return []
        return [
            path
            for path in directory.iterdir()
            if path.is_file()
            and (suffix is None or path.name.endswith(suffix))
            and not (exclude_hidden and path.name.startswith("."))
            and datetime.fromtimestamp(path.stat().st_mtime) < cutoff
        ]

    def _is_video(self, path: Path) -> bool:
        return self._is_managed_video_path(path) and not path.name.endswith(".part")

    def _is_managed_video_path(self, path: Path) -> bool:
        try:
            path.resolve().relative_to(self._videos_dir)
            return True
        except ValueError:
            return False

    @staticmethod
    def _read_json(path: Path) -> dict[str, str]:
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            return data if isinstance(data, dict) else {}
        except (FileNotFoundError, json.JSONDecodeError, OSError):
            return {}

    def _remove_json_keys(self, path: Path, keys: tuple[str, ...]) -> None:
        if not keys:
            return
        data = self._read_json(path)
        for key in keys:
            data.pop(key, None)
        path.write_text(json.dumps(data, indent=2), encoding="utf-8")
