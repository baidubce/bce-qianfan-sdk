import abc
from typing import Any, AsyncContextManager, ContextManager, Optional


class BaseRateLimiter(ContextManager, AsyncContextManager):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        if "key" in kwargs:
            key = kwargs["key"]
            self.acquire(key)

    @abc.abstractmethod
    def reset_once(self, rpm: float) -> None:
        ...

    @abc.abstractmethod
    async def async_reset_once(self, rpm: float) -> None:
        ...

    @abc.abstractmethod
    def acquire(self, key: Optional[str] = None) -> "BaseRateLimiter":
        ...
