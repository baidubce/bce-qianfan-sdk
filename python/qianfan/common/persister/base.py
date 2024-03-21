from abc import ABC, abstractmethod


class Persistent(ABC):
    @classmethod
    @abstractmethod
    def _space(cls) -> str:
        ...

    @abstractmethod
    def _identity(self) -> str:
        ...

    @abstractmethod
    def persist(self) -> bytes:
        ...

    @classmethod
    @abstractmethod
    def load(cls, b: bytes) -> "Persistent":
        ...
