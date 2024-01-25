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
base local data operator class
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Union

from qianfan.utils import log_error
from qianfan.utils.pydantic import BaseModel


class BaseLocalFilterOperator(ABC):
    """base class for data filtering"""

    def __init__(
        self, filter_column: str, text_language: str = "ZH", **kwargs: Any
    ) -> None:
        self.filter_column = filter_column
        self.text_language = text_language

    @abstractmethod
    def __call__(
        self,
        entry: Union[Dict[str, Any], List[Dict[str, Any]], str],
        *args: Any,
        **kwargs: Any,
    ) -> bool:
        """filter func"""

    def _get_real_document_from_entry(
        self, entry: Union[Dict[str, Any], List[Dict[str, Any]], str]
    ) -> str:
        if isinstance(entry, dict):
            return entry[self.filter_column]

        if isinstance(entry, str):
            return entry

        if isinstance(entry, list):
            err_msg = (
                "can't filter a list, please call unpack() of dataset object firstly"
                " before filtering"
            )
            log_error(err_msg)
            raise ValueError(err_msg)

        err_msg = f"unexpected entry type {type(entry)} for filtering"
        log_error(err_msg)
        raise ValueError(err_msg)


class BaseLocalMapOperator(BaseModel, ABC):
    """base class for data mapping"""

    @abstractmethod
    def __call__(
        self,
        entry: Union[Dict[str, Any], List[Dict[str, Any]], str],
        *args: Any,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """mapping func"""
