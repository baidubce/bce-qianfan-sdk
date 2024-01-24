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
base data source definition
"""

from abc import ABC, abstractmethod
from typing import Any, List, Union

from qianfan.dataset.data_source.data_source_utils import FormatType


class DataSource(ABC):
    """basic data source class"""

    @abstractmethod
    def save(self, data: str, **kwargs: Any) -> bool:
        """
        Export the data to the data source
        and return
        whether the import was successful or failed

        Args:
            data (str): data need to be saved
            **kwargs (Any): optional arguments

        Returns:
            bool: is saving successful
        """

    @abstractmethod
    async def asave(self, data: str, **kwargs: Any) -> bool:
        """
        Asynchronously export the data to the data source
        and return
        whether the import was successful or failed

        Args:
            data (str): data need to be saved
            **kwargs (Any): optional arguments

        Returns:
            bool: is saving successful
        """

    @abstractmethod
    def fetch(self, **kwargs: Any) -> Union[str, List[str]]:
        """
        Fetch data from source

        Args:
            **kwargs (Any): optional arguments

        Returns:
            Union[str, List[str]]: content retrieved from data source
        """

    @abstractmethod
    async def afetch(self, **kwargs: Any) -> Union[str, List[str]]:
        """
        Asynchronously fetch data from source

        Args:
            **kwargs (Any): optional arguments

        Returns:
            Union[str, List[str]]: content retrieved from data source
        """

    @abstractmethod
    def format_type(self) -> FormatType:
        """
        Get format type binding to source

        Returns:
            FormatType: format type binding to source
        """

    @abstractmethod
    def set_format_type(self, format_type: FormatType) -> None:
        """
        Set format type binding to source

        Args:
            format_type (FormatType): format type binding to source
        """
