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
from typing import Any, Callable, Optional, Sequence, Union

from typing_extensions import Self


class Processable(ABC):
    """
    make object 'processable'
    """

    @abstractmethod
    def map(self, op: Callable[[Any], Any]) -> Self:
        """
        map on a Processable object

        Args:
            op (Callable[[Any], Any]): handler used to map

        Returns:
            Self: a new Processable object after mapping
        """

    @abstractmethod
    def filter(self, op: Callable[[Any], bool]) -> Self:
        """
        filter on a Processable object

        Args:
            op (Callable[[Any], bool]): handler used to filter

        Returns:
            Self: a new Processable object after filtering
        """

    @abstractmethod
    def delete(self, index: Union[int, str]) -> Self:
        """
        delete an element from Processable object

        Args:
            index (Union[int, str]): element index to delete

        Returns:
            Self: a new Processable object after delete
        """


class Addable(ABC):
    """
    make object 'addable'
    """

    @abstractmethod
    def append(self, elem: Any) -> Self:
        """
        append an element at Appendable object

        Args:
            elem (Any): element to append

        Returns:
            Self: a new Addable object after appending
        """

    @abstractmethod
    def insert(self, elem: Any, index: Any) -> Self:
        """
        insert an element to Appendable object

        Args:
            elem (Any): element(s) to insert
            index (Any): where to insert element(s)

        Returns:
            Self: a new Addable object after inserting
        """


class Listable(ABC):
    """
    make object 'listable'
    """

    @abstractmethod
    def list(
        self, by: Optional[Union[slice, int, str, Sequence[int], Sequence[str]]] = None
    ) -> Any:
        """
        get an element from object

        Args:
            by (Optional[Union[slice, int, str, Sequence[int], Sequence[str]]):
                index used to get data or data list, default to None
        Returns:
            Any: elements
        """
