from .icache_manager import ICacheManager


class Cache:
    _cache_manager: ICacheManager

    def __init__(self, cache_manager: ICacheManager) -> None:
        self._cache_manager = cache_manager

    def read_as_text(self, key: str) -> str | None:
        path = self._cache_manager.get_for(key)
        return path.read_text() if path else None

    def read_as_bytes(self, key: str) -> bytes | None:
        path = self._cache_manager.get_for(key)
        return path.read_bytes() if path else None

    def save_as_text(self, key: str, content: str) -> None:
        path = self._cache_manager.get_for(key)
        if path is not None:
            path.write_text(content)
            return

        self._cache_manager.set_for(key)
        path = self._cache_manager.get_for(key)
        assert path is not None
        path.write_text(content)

    def save_as_bytes(self, key: str, content: bytes) -> None:
        path = self._cache_manager.get_for(key)
        if path is not None:
            path.write_bytes(content)
            return

        self._cache_manager.set_for(key)
        path = self._cache_manager.get_for(key)
        assert path is not None
        path.write_bytes(content)
