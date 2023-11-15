from abc import ABC, abstractmethod
from typing import Any, Callable, Optional, Sequence, Union

from typing_extensions import Self


class Processable(ABC):
    """
    所有可以被处理的对象需要实现的接口
    """

    @abstractmethod
    def map(self, op: Callable[[Any], Any]) -> Self:
        """对可处理对象做映射操作"""

    @abstractmethod
    def filter(self, op: Callable[[Any], bool]) -> Self:
        """对可处理对象做过滤操作"""

    @abstractmethod
    def delete(self, index: Union[int, str]) -> Self:
        """对可处理对象做删除操作"""


class Appendable(ABC):
    """
    所有可以追加元素的对象需要实现的接口
    """

    @abstractmethod
    def append(self, elem: Any) -> Self:
        """追加元素"""


class Listable(ABC):
    """
    所有支持获取子元素的对象需要实现的接口
    """

    @abstractmethod
    def list(
        self, by: Optional[Union[slice, int, str, Sequence[int], Sequence[str]]] = None
    ) -> Any:
        """支持使用多种方式来获取数据或者数据的一部分"""
