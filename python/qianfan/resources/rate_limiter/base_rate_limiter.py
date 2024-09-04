import abc
from typing import Any, AsyncContextManager, ContextManager, Optional


class BaseRateLimiter(abc.ABC, ContextManager, AsyncContextManager):
    @abc.abstractmethod
    def reset_once(self, rpm: float) -> None:
        ...

    @abc.abstractmethod
    async def async_reset_once(self, rpm: float) -> None:
        ...

    @abc.abstractmethod
    def __enter__(self) -> None:
        ...

    @abc.abstractmethod
    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        ...

    @abc.abstractmethod
    async def __aenter__(self) -> None:
        ...

    @abc.abstractmethod
    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        ...

    @abc.abstractmethod
    def acquire(self, key: Optional[str] = None) -> "BaseRateLimiter":
        ...
