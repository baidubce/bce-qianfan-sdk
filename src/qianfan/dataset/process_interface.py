# Copyright (c) 2023 Baidu, Inc. All Rights Reserved.
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
"""
interface file
"""

from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, Optional, Sequence, Union

from typing_extensions import Self


class Processable(ABC):
    """
    make object 'processable'
    """

    @abstractmethod
    def map(self, op: Callable[[Dict[str, Any]], Dict[str, Any]]) -> Self:
        """map on a Processable object"""

    @abstractmethod
    def filter(self, op: Callable[[Dict[str, Any]], bool]) -> Self:
        """filter on a Processable object"""

    @abstractmethod
    def delete(self, index: Union[int, str]) -> Self:
        """delete an element from Processable object"""


class Appendable(ABC):
    """
    make object 'appendable'
    """

    @abstractmethod
    def append(self, elem: Any) -> Self:
        """append an element at Appendable object"""


class Listable(ABC):
    """
    make object 'listable'
    """

    @abstractmethod
    def list(
        self, by: Optional[Union[slice, int, str, Sequence[int], Sequence[str]]] = None
    ) -> Any:
        """get an element from object"""
