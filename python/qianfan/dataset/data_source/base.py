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
from enum import Enum
from typing import Any, Optional

import pyarrow

from qianfan.dataset.table import Table


class FormatType(Enum):
    """Enum for data source format type"""

    Json = "json"
    Jsonl = "jsonl"
    Csv = "csv"
    # 无格式导出，一行就是一条数据，类似 Jsonl，但是非格式化
    Text = "txt"


class DataSource(ABC):
    """basic data source class"""

    @abstractmethod
    def save(self, table: Table, **kwargs: Any) -> bool:
        """
        Export the Table to the data source
        and return
        whether the import was successful or failed

        Args:
            table (Table): table need to be saved
            **kwargs (Any): optional arguments

        Returns:
            bool: is saving successful
        """

    @abstractmethod
    def load(self, **kwargs: Any) -> Optional[pyarrow.Table]:
        """
        Get a pyarrow.Table from current DataSource object, if it cloud.

        Args:
            **kwargs (Any): Arbitrary keyword arguments.

        Returns:
            Optional[pyarrow.Table]: A memory-mapped pyarrow.Table object or None
        """

    @abstractmethod
    def fetch(self, **kwargs: Any) -> pyarrow.Table:
        """
        Get a pyarrow.Table mandatorily

        Args:
            **kwargs (Any): Arbitrary keyword arguments.

        Returns:
            pyarrow.Table: table retrieved from file
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
