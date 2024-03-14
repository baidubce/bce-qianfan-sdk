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
bos data source implementation including uploading / downloading
"""

import json
import os
from typing import Any, Dict, Optional

import dateutil.parser
import pyarrow

from qianfan import get_config
from qianfan.config import encoding
from qianfan.dataset.consts import (
    QianfanDatasetBosDownloadingCacheDir,
    QianfanDatasetBosUploadingCacheDir,
)
from qianfan.dataset.data_source.base import DataSource, FormatType
from qianfan.dataset.data_source.file import FileDataSource
from qianfan.dataset.data_source.utils import (
    _get_a_memory_mapped_pyarrow_table,
    _read_all_file_from_zip,
    zip_file_or_folder,
)
from qianfan.dataset.table import Table
from qianfan.utils import log_error, log_info, log_warn
from qianfan.utils.bos_uploader import BosHelper
from qianfan.utils.pydantic import BaseModel, Field, root_validator


class BosDataSource(DataSource, BaseModel):
    """Bos Data Source"""

    region: str
    bucket: str
    bos_file_path: str
    file_format: Optional[FormatType] = Field(default=None)
    ak: Optional[str] = Field(default=None)
    sk: Optional[str] = Field(default=None)

    def save(
        self,
        table: Table,
        should_save_as_zip_file: bool = False,
        should_overwrite_existed_file: bool = False,
        should_use_qianfan_special_jsonl_format: bool = False,
        **kwargs: Any,
    ) -> bool:
        """
        Export the data to specific bos storage
        and return
        whether the import was successful or failed

        Args:
            table (pyarrow.Table):
                data waiting to be uploaded.
            should_save_as_zip_file (bool):
                whether upload table as a zip file after serialization.
                when format is txt, an entry in table will become to
                an individual file in zip file.
            should_overwrite_existed_file (bool):
                should bos data source overwrite existed file when save data,
                default to False
            should_use_qianfan_special_jsonl_format (bool):
                whether bos should use the special format for uploaded
                jsonl file, default to False, only available when file format is jsonl.
                if you want to use uploaded file as training set, please set
                this bool value.
            **kwargs (Any):
                optional arguments

        Returns:
            bool: is saving successful
        """
        # 特判一下，防止用户手滑设置了出现意外情况
        if (
            should_use_qianfan_special_jsonl_format
            and self.format_type() != FormatType.Jsonl
        ):
            should_use_qianfan_special_jsonl_format = False

        assert self.ak
        assert self.sk
        assert self.file_format

        bos_helper = BosHelper(self.region, self.ak, self.sk)

        # 构建远端的 Bos 路径
        if not should_save_as_zip_file:
            final_bos_file_path = self.bos_file_path

        else:
            final_bos_file_path = self.bos_file_path.replace(
                f".{self.file_format.value}", ".zip"
            )

        log_info(
            f"start to upload file to bos path: {final_bos_file_path} in bucket"
            f" {self.bucket}"
        )

        # 检查 BOS 上是否已经存在文件
        if not should_overwrite_existed_file:
            file_existed = bos_helper.check_if_file_existed_on_bos(
                self.bucket, final_bos_file_path
            )

            if file_existed:
                err_msg = (
                    f"{final_bos_file_path} existed and argument"
                    " 'should_overwrite_existed_file' is False"
                )
                log_error(err_msg)
                raise ValueError(err_msg)

        # 如果设置了 should_overwrite_existed_file 则防御性删除文件
        if should_overwrite_existed_file:
            log_info(
                f"try to delete original bos file {final_bos_file_path} for overwrite"
            )
            bos_helper.delete_bos_file_anyway(self.bucket, final_bos_file_path)

        # 构造本地的缓存路径
        local_file_path = os.path.join(
            self._get_specific_uploading_cache_path(),
            os.path.split(final_bos_file_path)[1],
        )

        # 在特定情况下修改格式
        if table.is_dataset_grouped() and should_use_qianfan_special_jsonl_format:
            table.pack()

        FileDataSource(
            path=local_file_path,
            file_format=self.format_type(),
            save_as_folder=should_save_as_zip_file,
        ).save(
            table,
            use_qianfan_special_jsonl_format=should_use_qianfan_special_jsonl_format,
            **kwargs,
        )

        # 打压缩包
        if should_save_as_zip_file:
            local_file_path = zip_file_or_folder(local_file_path)

        try:
            log_info(
                f"start to upload file {local_file_path} to bos {final_bos_file_path}"
            )
            bos_helper.upload_file_to_bos(
                local_file_path, final_bos_file_path, self.bucket
            )
        except Exception as e:
            err_msg = (
                "an error occurred during upload data to bos with path"
                f" {final_bos_file_path} of bucket {self.bucket} in region"
                f" {self.region}: {str(e)}"
            )
            log_error(err_msg)
            raise e

        return True

    def _get_specific_uploading_cache_path(self) -> str:
        bos_file_path = os.path.split(self.bos_file_path[1:])[0]
        cache_path = os.path.join(
            QianfanDatasetBosUploadingCacheDir, self.region, self.bucket, bos_file_path
        )
        os.makedirs(cache_path, exist_ok=True)

        return cache_path

    def _get_specific_downloading_cache_path(self) -> str:
        bos_file_path = self.bos_file_path[1:]
        cache_path = os.path.join(
            QianfanDatasetBosDownloadingCacheDir,
            self.region,
            self.bucket,
            bos_file_path,
        )
        os.makedirs(cache_path, exist_ok=True)

        return cache_path

    def _check_bos_file_cache(self, bos_helper: BosHelper) -> bool:
        cache_path = self._get_specific_downloading_cache_path()

        meta_info_path = os.path.join(cache_path, "info.json")
        if not os.path.exists(meta_info_path):
            return False

        with open(meta_info_path, mode="r", encoding=encoding()) as f:
            cache_meta_info = json.loads(f.read())

        if "last_modified" not in cache_meta_info:
            return False

        parser = dateutil.parser.parser()
        cache_last_modified_time = parser.parse(cache_meta_info["last_modified"])

        new_meta_info = bos_helper.get_metadata(self.bucket, self.bos_file_path)
        new_last_modified_time = parser.parse(new_meta_info["last_modified"])

        return cache_last_modified_time >= new_last_modified_time

    def _update_file_cache(self, bos_helper: BosHelper) -> None:
        cache_path = self._get_specific_downloading_cache_path()
        cache_content_path = os.path.join(cache_path, "content")
        cache_meta_info_path = os.path.join(cache_path, "info.json")

        bos_helper.get_object_as_file(
            self.bucket, self.bos_file_path, cache_content_path
        )

        meta_info_obj = bos_helper.get_metadata(self.bucket, self.bos_file_path)
        with open(cache_meta_info_path, mode="w", encoding=encoding()) as f:
            f.write(json.dumps(meta_info_obj, ensure_ascii=False))

        return

    def _read_from_cache(self, is_read_from_zip: bool, **kwargs: Any) -> pyarrow.Table:
        cache_path = self._get_specific_downloading_cache_path()
        cache_content_path = os.path.join(cache_path, "content")

        if is_read_from_zip:
            return _read_all_file_from_zip(
                cache_content_path, self.format_type(), **kwargs
            )

        return _get_a_memory_mapped_pyarrow_table(
            cache_content_path, self.format_type(), **kwargs
        )

    def fetch(self, read_from_zip: bool = False, **kwargs: Any) -> pyarrow.Table:
        """
        Read data from bos mandatorily.

        Args:
            read_from_zip (bool):
                does FileDataSource read data from a zip file,
                default to False
            **kwargs (Any): Arbitrary keyword arguments.

        Returns:
            pyarrow.Table: A memory-mapped pyarrow.Table object
        """
        assert self.ak
        assert self.sk
        assert self.file_format

        bos_helper = BosHelper(self.region, self.ak, self.sk)

        # 检查缓存并且在缓存失效的情况下更新
        if not self._check_bos_file_cache(bos_helper):
            log_info("cache was outdated, start to update bos cache")
            self._update_file_cache(bos_helper)

        # 检查是否是从一个压缩包读取文件
        index = self.bos_file_path.rfind(".")
        read_from_zip = read_from_zip or (
            index != -1 and self.bos_file_path[index + 1 :] == "zip"
        )

        log_info(
            f"ready to fetch a file from bos path: {self.bos_file_path} in bucket"
            f" {self.bucket}"
        )

        try:
            return self._read_from_cache(read_from_zip, **kwargs)
        except Exception as e:
            err_msg = (
                f"fetch file content from bos path {self.bos_file_path} of bucket"
                f" {self.bucket} in region {self.region} failed: {str(e)}"
            )
            log_error(err_msg)
            raise e

    def load(self, **kwargs: Any) -> Optional[pyarrow.Table]:
        """
        Get a pyarrow.Table from current DataSource object

        Args:
            **kwargs (Any): Arbitrary keyword arguments.

        Returns:
            Optional[pyarrow.Table]: A memory-mapped pyarrow.Table object or None
        """
        return None

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
    @classmethod
    def _param_check(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        ak = values.get("ak", None)
        if not ak:
            values["ak"] = get_config().ACCESS_KEY

        sk = values.get("sk", None)
        if not sk:
            values["sk"] = get_config().SECRET_KEY

        bos_file_path = values["bos_file_path"]
        if bos_file_path[-1] == "/":
            err_msg = f"bos file path {bos_file_path} end with '/'"
            log_error(err_msg)
            raise ValueError(err_msg)

        if values.get("file_format", None):
            return values

        index = bos_file_path.rfind(".")
        # 查询不到或者是 zip 包的情况下默认使用纯文本格式
        if index == -1 or bos_file_path[index + 1 :] == "zip":
            log_warn(f"use default format type {FormatType.Text}")
            values["file_format"] = FormatType.Text
        else:
            suffix = bos_file_path[index + 1 :]
            for t in FormatType:
                if t.value == suffix:
                    values["file_format"] = t
                    log_info(f"use format type {t}")
                    return values
            err_msg = f"cannot match proper format type for {suffix}"
            log_error(err_msg)
            raise ValueError(err_msg)

        return values
