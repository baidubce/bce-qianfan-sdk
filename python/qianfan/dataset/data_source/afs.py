import hashlib
import json
import os
from typing import Any, Optional

import dateutil
import pyarrow

from qianfan.config import encoding
from qianfan.dataset.consts import (
    QianfanDatasetAFSDownloadingCacheDir,
    QianfanDatasetAFSUploadingCacheDir,
    _merge_custom_path,
)
from qianfan.dataset.data_source.base import DataSource, FormatType
from qianfan.dataset.data_source.utils import (
    _get_a_pyarrow_table,
    _pack_a_table_into_file_for_uploading,
    _read_all_file_from_zip,
    _read_all_image_from_zip,
)
from qianfan.dataset.table import Table
from qianfan.resources.batch_inference.helper.helper import AFSClient
from qianfan.utils import log_error, log_info, log_warn
from qianfan.utils.pydantic import BaseModel, Field

try:
    import dateutil.parser
except ImportError:
    log_warn("python-dateutil isn't installed, only online function can be used")


class AFSDataSource(DataSource, BaseModel):
    host: str
    ugi: str
    afs_file_path: str
    file_format: Optional[FormatType] = Field(default=None)

    def save(
        self,
        table: Table,
        should_save_as_zip_file: bool = False,
        should_overwrite_existed_file: bool = False,
        should_use_qianfan_special_jsonl_format: bool = False,
        **kwargs: Any,
    ) -> bool:
        # 特判一下，防止用户手滑设置了出现意外情况
        if (
            should_use_qianfan_special_jsonl_format
            and self.format_type() != FormatType.Jsonl
        ):
            should_use_qianfan_special_jsonl_format = False

        # 如果是文生图，则需要强制上压缩包
        if self.format_type() == FormatType.Text2Image:
            should_save_as_zip_file = True

        assert self.file_format

        afs_client = AFSClient(host=self.host, ugi=self.ugi)

        # 构建远端的 AFS 路径
        if not should_save_as_zip_file:
            final_afs_file_path = self.afs_file_path

        else:
            final_afs_file_path = self.afs_file_path.replace(
                f".{self.file_format.value}", ".zip"
            )

        log_info(
            f"start to upload file to afs path: {final_afs_file_path} in host"
            f" {self.host}"
        )

        # 检查 AFS 上是否已经存在文件
        if not should_overwrite_existed_file:
            file_existed = afs_client.test(self.afs_file_path, "-e")

            if file_existed == 0:
                err_msg = (
                    f"{final_afs_file_path} existed and argument"
                    " 'should_overwrite_existed_file' is False"
                )
                log_error(err_msg)
                raise ValueError(err_msg)

        # 如果设置了 should_overwrite_existed_file 则防御性删除文件
        if should_overwrite_existed_file:
            log_info(
                f"try to delete original afs file {final_afs_file_path} for overwrite"
            )
            try:
                afs_client.rm(self.afs_file_path)
            except ValueError:
                # do nothing
                ...

        # 构造本地的缓存路径
        local_file_path = os.path.join(
            self._get_specific_uploading_cache_path(),
            os.path.split(final_afs_file_path)[1],
        )

        local_file_path = _pack_a_table_into_file_for_uploading(
            table,
            local_file_path,
            self.file_format,
            should_save_as_zip_file,
            should_use_qianfan_special_jsonl_format,
        )

        try:
            log_info(
                f"start to upload file {local_file_path} to afs {final_afs_file_path}"
            )
            afs_client.put(local_file_path, final_afs_file_path)
        except Exception as e:
            err_msg = (
                "an error occurred during upload data to afs with path"
                f" {final_afs_file_path} of host {self.host}: {str(e)}"
            )
            log_error(err_msg)
            raise e

        return True

    def fetch(self, read_from_zip: bool = False, **kwargs: Any) -> pyarrow.Table:
        assert self.file_format

        afs_client = AFSClient(host=self.host, ugi=self.ugi)
        if not self._check_afs_file_cache(afs_client):
            log_info("cache was outdated, start to update afs cache")
            self._update_file_cache(afs_client)

        # 检查是否是从一个压缩包读取文件
        index = self.afs_file_path.rfind(".")
        read_from_zip = read_from_zip or (
            index != -1 and self.afs_file_path[index + 1 :] == "zip"
        )

        log_info(
            f"ready to fetch a file from afs path: {self.afs_file_path} in host"
            f" {self.host}"
        )

        try:
            return self._read_from_cache(read_from_zip, **kwargs)
        except Exception as e:
            err_msg = (
                f"fetch file content from afs path {self.afs_file_path} of host"
                f" {self.host} failed: {str(e)}"
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

    def _get_specific_downloading_cache_path(self) -> str:
        cache_path = os.path.join(
            _merge_custom_path(QianfanDatasetAFSDownloadingCacheDir),
            hashlib.md5(
                bytes(self.host + self.afs_file_path, encoding="utf8")
            ).hexdigest(),
        )
        os.makedirs(cache_path, exist_ok=True)

        return cache_path

    def _get_specific_uploading_cache_path(self) -> str:
        cache_path = os.path.join(
            _merge_custom_path(QianfanDatasetAFSUploadingCacheDir),
            hashlib.md5(
                bytes(self.host + self.afs_file_path, encoding="utf8")
            ).hexdigest(),
        )
        os.makedirs(cache_path, exist_ok=True)

        return cache_path

    def _get_downloaded_content_cache_path(self) -> str:
        cache_path = self._get_specific_downloading_cache_path()
        return os.path.join(cache_path, "content")

    def _get_downloaded_content_metainfo_path(self) -> str:
        cache_path = self._get_specific_downloading_cache_path()
        return os.path.join(cache_path, "info.json")

    def _check_afs_file_cache(self, afs_client: AFSClient) -> bool:
        meta_info_path = self._get_downloaded_content_metainfo_path()
        if not os.path.exists(meta_info_path):
            return False

        with open(meta_info_path, mode="r", encoding=encoding()) as f:
            cache_meta_info = json.loads(f.read())

        if "last_modified" not in cache_meta_info:
            return False

        parser = dateutil.parser.parser()
        cache_last_modified_time = parser.parse(cache_meta_info["last_modified"])
        new_last_modified_time = parser.parse(
            afs_client.get_modify_time(self.afs_file_path)
        )

        return cache_last_modified_time >= new_last_modified_time

    def _update_file_cache(self, afs_client: AFSClient) -> None:
        cache_content_path = self._get_downloaded_content_cache_path()
        cache_meta_info_path = self._get_downloaded_content_metainfo_path()

        afs_client.get(self.afs_file_path, cache_content_path)
        parser = dateutil.parser.parser()
        new_last_modified_time = parser.parse(
            afs_client.get_modify_time(self.afs_file_path)
        )

        with open(cache_meta_info_path, mode="w", encoding=encoding()) as f:
            f.write(
                json.dumps(
                    {
                        "last_modified": new_last_modified_time.strftime(
                            "%Y-%m-%d %H:%M:%S"
                        )
                    },
                    ensure_ascii=False,
                )
            )

        return

    def _read_from_cache(self, is_read_from_zip: bool, **kwargs: Any) -> pyarrow.Table:
        cache_content_path = self._get_downloaded_content_cache_path()

        if self.format_type() == FormatType.Text2Image:
            return _read_all_image_from_zip(cache_content_path)

        if is_read_from_zip:
            return _read_all_file_from_zip(
                cache_content_path, self.format_type(), **kwargs
            )

        return _get_a_pyarrow_table(cache_content_path, self.format_type(), **kwargs)
