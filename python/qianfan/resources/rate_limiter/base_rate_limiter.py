import abc
from typing import AsyncContextManager, ContextManager, Optional


class BaseRateLimiter(ContextManager, AsyncContextManager):
    @abc.abstractmethod
    def reset_once(self, rpm: float) -> None:
        ...

    @abc.abstractmethod
    async def async_reset_once(self, rpm: float) -> None:
        ...

    @abc.abstractmethod
    def acquire(self, key: Optional[str] = None) -> "BaseRateLimiter":
        ...
