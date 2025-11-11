from abc import ABC, abstractmethod


class BaseOutput(ABC):
    @abstractmethod
    def write(self) -> None:
        raise NotImplementedError
