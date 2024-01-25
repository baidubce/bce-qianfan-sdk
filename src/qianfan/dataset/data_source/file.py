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
file data source implementation
"""

import os
import uuid
import zipfile
from typing import Any, Dict, List, Optional, Union

from qianfan.config import encoding
from qianfan.dataset.data_source import DataSource, FormatType
from qianfan.dataset.data_source.utils import (
    _read_all_file_content_in_an_folder,
    _read_all_file_from_zip,
)
from qianfan.utils import log_error, log_info, log_warn
from qianfan.utils.pydantic import BaseModel, Field, root_validator


class FileDataSource(DataSource, BaseModel):
    """file data source"""

    path: str
    file_format: Optional[FormatType] = Field(default=None)
    save_as_folder: bool = Field(default=False)

    def save(self, data: Union[str, List[str]], **kwargs: Any) -> bool:
        """
        Write data to file。

        Args:
            data (Union[str, List[str]]): data waiting to be written。
            **kwargs (Any): optional arguments。

        Returns:
            bool: has data been written successfully
        """
        if isinstance(data, str):
            if os.path.isdir(self.path):
                file_path = os.path.join(
                    self.path, f"data_{uuid.uuid4()}.{self.format_type().value}"
                )
            else:
                file_path = self.path
            with open(file_path, mode="w", encoding=encoding()) as file:
                file.write(data)
            return True
        else:
            os.makedirs(self.path)
            for index in range(len(data)):
                entry = data[index]
                with open(
                    os.path.join(
                        self.path, f"entry_{index}.{self.format_type().value}"
                    ),
                    mode="w",
                    encoding=encoding(),
                ) as file:
                    file.write(entry)
            return True

    async def asave(self, data: Union[str, List[str]], **kwargs: Any) -> bool:
        """
        Asynchronously Write data to file。
        Not available currently

        Args:
            data (Union[str, List[str]]): data waiting to be written。
            **kwargs (Any): optional arguments。

        Returns:
            bool: has data been written successfully
        """
        raise NotImplementedError()

    def fetch(self, **kwargs: Any) -> Union[str, List[str]]:
        """
        Read data from file.

        Args:
            **kwargs (Any): Arbitrary keyword arguments.

        Returns:
            Union[str, List[str]]:
                String or list of string containing the data read from the file.
        """
        # 检查文件是否存在且非目录
        assert self.file_format
        read_from_zip = zipfile.is_zipfile(self.path)

        if not os.path.exists(self.path):
            raise ValueError("file path not found")
        if os.path.isdir(self.path):
            return _read_all_file_content_in_an_folder(self.path, self.file_format)
        elif read_from_zip:
            return _read_all_file_from_zip(self.path, self.file_format)
        else:
            with open(self.path, mode="r", encoding=encoding()) as file:
                return file.read().strip("\n")

    async def afetch(self, **kwargs: Any) -> Union[str, List[str]]:
        """
        Asynchronously Read data from file.
        Not available currently

        Args:
            **kwargs (Any): Arbitrary keyword arguments.

        Returns:
            Union[str, List[str]]:
                String or list of string containing the data read from the file.
        """
        raise NotImplementedError()

    def format_type(self) -> FormatType:
        """
        Get format type binding to source

        Returns:
            FormatType: format type binding to source
        """
        assert self.file_format
        return self.file_format

    def set_format_type(self, format_type: FormatType) -> None:
        """
        Set format type binding to source

        Args:
            format_type (FormatType): format type binding to source
        """
        self.file_format = format_type

    @root_validator
    def _format_check(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        if values["file_format"]:
            return values

        path = values["path"]

        try:
            index = path.rfind(".")
            # 读文件夹或查询不到或读 zip 包的情况下默认使用纯文本格式
            if os.path.isdir(path) or index == -1 or path[index + 1 :] == "zip":
                log_warn(f"use default format type {FormatType.Text}")
                values["file_format"] = FormatType.Text
                return values
            suffix = path[index + 1 :]
            for t in FormatType:
                if t.value == suffix:
                    values["file_format"] = t
                    log_info(f"use format type {t}")
                    return values
            raise ValueError(f"cannot match proper format type for {suffix}")
        except Exception as e:
            log_error(str(e))
            raise e
