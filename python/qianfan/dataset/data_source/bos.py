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
from typing import Any, Dict, List, Optional, Union

import dateutil.parser

from qianfan import get_config
from qianfan.config import encoding
from qianfan.dataset.consts import QianfanDatasetLocalCacheDir
from qianfan.dataset.data_source.base import DataSource, FormatType
from qianfan.dataset.data_source.utils import (
    _check_data_and_zip_file_valid,
    _read_all_file_from_zip,
)
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
        data: Optional[str] = None,
        zip_file_path: Optional[str] = None,
        should_overwrite_existed_file: bool = False,
        **kwargs: Any,
    ) -> bool:
        """
        Export the data to specific bos storage
        and return
        whether the import was successful or failed

        Args:
            data (Optional[str]):
                data need to be saved, default to None
            zip_file_path (Optional[str]):
                path of your zip file, default to None
            should_overwrite_existed_file (bool):
                should bos data source overwrite existed file when save data,
                default to False
            **kwargs (Any):
                optional arguments

        Returns:
            bool: is saving successful
        """
        assert self.ak
        assert self.sk
        assert self.file_format

        bos_helper = BosHelper(self.region, self.ak, self.sk)

        _check_data_and_zip_file_valid(data, zip_file_path)

        if data:
            final_bos_file_path = self.bos_file_path
            log_info(
                f"ready to fetch a file from bos path: {final_bos_file_path} in bucket"
                f" {self.bucket}"
            )
        else:
            final_bos_file_path = self.bos_file_path.replace(
                f".{self.file_format.value}", ".zip"
            )
            log_info(
                f"ready to fetch a zip file from bos path: {final_bos_file_path} in"
                f" bucket {self.bucket}"
            )

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

        if should_overwrite_existed_file:
            log_info(
                f"try to delete original bos file {final_bos_file_path} for overwrite"
            )
            bos_helper.delete_bos_file_anyway(self.bucket, final_bos_file_path)

        try:
            if data:
                log_info("fetch file content directly from bos file")
                bos_helper.upload_content_to_bos(data, final_bos_file_path, self.bucket)
            elif zip_file_path:
                log_info("start to fetch zip file from bos")
                bos_helper.upload_file_to_bos(
                    zip_file_path, final_bos_file_path, self.bucket
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

    async def asave(self, data: str, **kwargs: Any) -> bool:
        """
        Asynchronously export the data to specific bos storage
        and return
        whether the import was successful or failed
        Not available currently

        Args:
            data (str): data need to be saved
            **kwargs (Any): optional arguments

        Returns:
            bool: is saving successful
        """
        raise NotImplementedError()

    def _get_specific_cache_path(self) -> str:
        bos_file_path = self.bos_file_path[1:]
        cache_path = os.path.join(
            QianfanDatasetLocalCacheDir, self.region, self.bucket, bos_file_path
        )
        if not os.path.exists(cache_path):
            os.makedirs(cache_path)

        return cache_path

    def _check_bos_file_cache(self, bos_helper: BosHelper) -> bool:
        cache_path = self._get_specific_cache_path()

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
        cache_path = self._get_specific_cache_path()
        cache_content_path = os.path.join(cache_path, "content")
        cache_meta_info_path = os.path.join(cache_path, "info.json")

        bos_helper.get_object_as_file(
            self.bucket, self.bos_file_path, cache_content_path
        )

        meta_info_obj = bos_helper.get_metadata(self.bucket, self.bos_file_path)
        with open(cache_meta_info_path, mode="w", encoding=encoding()) as f:
            f.write(json.dumps(meta_info_obj, ensure_ascii=False))

        return

    def _read_from_cache(self, is_read_from_zip: bool) -> Union[List[str], str]:
        cache_path = self._get_specific_cache_path()
        cache_content_path = os.path.join(cache_path, "content")

        if is_read_from_zip:
            return _read_all_file_from_zip(cache_content_path, self.format_type())

        with open(cache_content_path, mode="r", encoding=encoding()) as f:
            return f.read()

    def fetch(
        self, read_from_zip: bool = False, **kwargs: Any
    ) -> Union[str, List[str]]:
        """
        Read data from bos.

        Args:
            read_from_zip (bool):
                does FileDataSource read data from a zip file,
                default to False
            **kwargs (Any): Arbitrary keyword arguments.

        Returns:
            Union[str, List[str]]:
                String or list of string containing the data read from the file.
        """
        assert self.ak
        assert self.sk
        assert self.file_format

        bos_helper = BosHelper(self.region, self.ak, self.sk)
        if not self._check_bos_file_cache(bos_helper):
            log_info("cache was outdated, start to update bos cache")
            self._update_file_cache(bos_helper)

        index = self.bos_file_path.rfind(".")
        read_from_zip = read_from_zip or (
            index != -1 and self.bos_file_path[index + 1 :] == "zip"
        )

        if read_from_zip:
            log_info(
                f"ready to fetch a zip file from bos path: {self.bos_file_path} in"
                f" bucket {self.bucket}"
            )
        else:
            log_info(
                f"ready to fetch a file from bos path: {self.bos_file_path} in bucket"
                f" {self.bucket}"
            )

        try:
            return self._read_from_cache(read_from_zip)
        except Exception as e:
            err_msg = (
                f"fetch file content from bos path {self.bos_file_path} of bucket"
                f" {self.bucket} in region {self.region} failed: {str(e)}"
            )
            log_error(err_msg)
            raise e

    async def afetch(self, **kwargs: Any) -> Union[str, List[str]]:
        """
        Asynchronously Read data from bos.
        Not available currently

        Args:
            **kwargs (Any): Arbitrary keyword arguments.

        Returns:
            Union[str, List[str]]:
                String or list of string containing the data read from the file.
        """
        raise NotImplementedError()

    def format_type(self) -> FormatType:
        assert self.file_format
        return self.file_format

    def set_format_type(self, format_type: FormatType) -> None:
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
