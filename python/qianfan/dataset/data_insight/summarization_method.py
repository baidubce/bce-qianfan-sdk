from abc import ABC, abstractmethod
from typing import Any, List

from qianfan.dataset import Dataset


class SummarizationMethod(ABC):
    """do nothing"""

    name: str = "basic"

    @abstractmethod
    def calculate(self, ds: Dataset, columns: List[str], **kwargs: Any) -> List[Any]:
        """do calculation"""


class MeanMethod(SummarizationMethod):
    """calculate mean value"""

    name: str = "mean"

    def calculate(self, ds: Dataset, columns: List[str], **kwargs: Any) -> List[float]:
        return [ds.mean(column=column, **kwargs) for column in columns]


class QuantileMethod(SummarizationMethod):
    """calculate quantile"""

    def __init__(self, q: float):
        self.q = q
        self.name = f"{q * 100}_quantile"

    def calculate(self, ds: Dataset, columns: List[str], **kwargs: Any) -> List[float]:
        return [
            ds.quantile(column=column, q=[self.q], **kwargs)[0] for column in columns
        ]


class MinMethod(SummarizationMethod):
    """calculate min value"""

    name: str = "min"

    def calculate(self, ds: Dataset, columns: List[str], **kwargs: Any) -> List[float]:
        return [ds.min(column, **kwargs) for column in columns]


class MaxMethod(SummarizationMethod):
    """calculate min value"""

    name: str = "max"

    def calculate(self, ds: Dataset, columns: List[str], **kwargs: Any) -> List[float]:
        return [ds.max(column, **kwargs) for column in columns]
