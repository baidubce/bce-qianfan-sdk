# Copyright (c) 2024 Baidu, Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""summarization method"""

from abc import ABC, abstractmethod
from typing import Any, List


class SummarizationMethod(ABC):
    """do nothing"""

    name: str = "basic"

    @abstractmethod
    def calculate(self, ds: Any, columns: List[str], **kwargs: Any) -> List[Any]:
        """do calculation"""


class MeanMethod(SummarizationMethod):
    """calculate mean value"""

    name: str = "mean"

    def calculate(self, ds: Any, columns: List[str], **kwargs: Any) -> List[float]:
        return [ds.mean(column=column, **kwargs) for column in columns]


class QuantileMethod(SummarizationMethod):
    """calculate quantile"""

    def __init__(self, q: float):
        self.q = q
        self.name = f"{q * 100}_quantile"

    def calculate(self, ds: Any, columns: List[str], **kwargs: Any) -> List[float]:
        return [
            ds.quantile(column=column, q=[self.q], **kwargs)[0] for column in columns
        ]


class MinMethod(SummarizationMethod):
    """calculate min value"""

    name: str = "min"

    def calculate(self, ds: Any, columns: List[str], **kwargs: Any) -> List[float]:
        return [ds.min(column, **kwargs) for column in columns]


class MaxMethod(SummarizationMethod):
    """calculate min value"""

    name: str = "max"

    def calculate(self, ds: Any, columns: List[str], **kwargs: Any) -> List[float]:
        return [ds.max(column, **kwargs) for column in columns]
