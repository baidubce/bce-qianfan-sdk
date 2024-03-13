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
import io
import json
import os
import zipfile
from typing import Any, Dict, List, Optional, TextIO, Union

import clevercsv
import pyarrow

from qianfan.config import encoding
from qianfan.dataset.data_source.base import DataSource, FormatType
from qianfan.dataset.data_source.utils import (
    _get_a_memory_mapped_pyarrow_table,
    _read_all_file_content_in_an_folder,
    _read_all_file_from_zip,
    zip_file_or_folder,
)
from qianfan.dataset.table import Table
from qianfan.utils import log_error, log_info, log_warn
from qianfan.utils.pydantic import BaseModel, Field, root_validator


class FileDataSource(DataSource, BaseModel):
    """file data source"""

    path: str
    file_format: Optional[FormatType] = Field(default=None)

    # Available only when 'file_format' is Text
    # and 'path' points to a folder
    # This option will convert single row in table into a separate file
    # in a folder
    save_as_folder: bool = Field(default=False)

    def _write_as_format(
        self,
        fd: TextIO,
        data: Union[List[Dict[str, Any]], List[List[Dict[str, Any]]], List[str]],
        index: int,
        use_qianfan_special_jsonl_format: bool,
    ) -> None:
        lines: List[str] = []
        if self.file_format == FormatType.Json:
            if index != 0:
                lines.append(",\n")
            for i in range(len(data)):
                lines.append(json.dumps(data[i], ensure_ascii=False))
                if i != len(data) - 1:
                    lines.append(",\n")

            fd.writelines(lines)

        elif self.file_format == FormatType.Jsonl:
            if index != 0:
                lines.append("\n")

            is_list = True if data and isinstance(data[0], list) else False
            for i in range(len(data)):
                if use_qianfan_special_jsonl_format and not is_list:
                    lines.append(f"[{json.dumps(data[i], ensure_ascii=False)}]")
                else:
                    lines.append(json.dumps(data[i], ensure_ascii=False))
                if i != len(data) - 1:
                    lines.append("\n")

            fd.writelines(lines)

        elif self.file_format == FormatType.Csv:
            assert isinstance(data[0], dict)

            string_stream_buffer = io.StringIO()
            csv_writer = clevercsv.DictWriter(
                string_stream_buffer, fieldnames=list(data[0].keys())
            )

            # 如果是第一次写入，则需要加上 header 部分
            if index == 0:
                csv_writer.writeheader()
            csv_writer.writerows(data)  # type: ignore
            fd.write(string_stream_buffer.getvalue())

        elif self.file_format == FormatType.Text:
            for elem in data:
                assert isinstance(elem, str)
                fd.write(elem)
                fd.write("\n")
        else:
            err_msg = "unexpected format"
            log_error(err_msg)
            raise ValueError(err_msg)

    def _save_generic_text_into_folder(
        self, table: Table, batch_size: int = 10, **kwargs: Any
    ) -> bool:
        os.makedirs(self.path, exist_ok=True)

        for i in range(0, table.row_number(), batch_size):
            table_slice = list(table.list(slice(i, i + batch_size - 1)))
            for j in range(min(batch_size, len(table_slice))):
                with open(
                    os.path.join(self.path, f"{i + j}.txt"),
                    mode="w",
                    encoding=encoding(),
                ) as f:
                    f.write(table_slice[j])

        return True

    def save(
        self,
        table: Table,
        batch_size: int = 10000,
        use_qianfan_special_jsonl_format: bool = False,
        **kwargs: Any,
    ) -> bool:
        """
        Write data to file。

        Args:
            table (Table):
                data waiting to be uploaded.
            batch_size (int):
                the batch size used when
                writing entry to file in batch
            use_qianfan_special_jsonl_format (bool):
                whether writer use qianfan special format
                when write jsonline data, default to False
            **kwargs (Any): optional arguments。

        Returns:
            bool: has data been written successfully
        """
        if self.save_as_folder and self.file_format == FormatType.Text:
            return self._save_generic_text_into_folder(table, batch_size, **kwargs)

        # 有可能文件路径的父文件夹不存在，得先创建
        os.makedirs(os.path.abspath(os.path.dirname(self.path)), exist_ok=True)

        with open(
            self.path,
            mode="w",
            encoding=encoding() if self.file_format != FormatType.Csv else "utf-8-sig",
        ) as f:
            # Json 格式的时候需要特判
            if self.file_format == FormatType.Json:
                f.write("[\n")

            for i in range(0, table.row_number(), batch_size):
                self._write_as_format(
                    f,
                    table.list(slice(i, i + batch_size - 1)),
                    i,
                    use_qianfan_special_jsonl_format,
                )

            # Json 格式的时候需要特判
            if self.file_format == FormatType.Json:
                f.write("\n]")

        return True

    def _zip_file_or_folder(self) -> str:
        return zip_file_or_folder(self.path)

    def fetch(self, **kwargs: Any) -> pyarrow.Table:
        """
        Get a pyarrow.Table mandatorily

        Args:
            **kwargs (Any): Arbitrary keyword arguments.

        Returns:
            pyarrow.Table: table retrieved from file
        """
        ret = self.load(**kwargs)
        assert ret
        return ret

    def load(self, **kwargs: Any) -> Optional[pyarrow.Table]:
        """
        Get a pyarrow.Table from current DataSource object

        Args:
            **kwargs (Any): Arbitrary keyword arguments.

        Returns:
            Optional[pyarrow.Table]: A memory-mapped pyarrow.Table object or None
        """

        # 如果是单个文件，直接读取
        assert isinstance(self.file_format, FormatType)

        if not os.path.isdir(self.path):
            return _get_a_memory_mapped_pyarrow_table(
                self.path, self.file_format, **kwargs
            )

        # 如果是个压缩包，则需要先解压再读取
        if zipfile.is_zipfile(self.path):
            return _read_all_file_from_zip(self.path, self.file_format, **kwargs)

        # 如果是个文件夹，则遍历读取并且合并表格
        return _read_all_file_content_in_an_folder(
            self.path, self.file_format, **kwargs
        )

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
