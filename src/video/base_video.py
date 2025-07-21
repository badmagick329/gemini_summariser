from abc import ABC, abstractmethod
from pathlib import Path


class BaseVideo(ABC):
    @property
    @abstractmethod
    def path(self) -> Path:
        raise NotImplementedError("Subclasses must implement the path method")

    @property
    @abstractmethod
    def video_id(self) -> str:
        raise NotImplementedError("Subclasses must implement the video_id property")
