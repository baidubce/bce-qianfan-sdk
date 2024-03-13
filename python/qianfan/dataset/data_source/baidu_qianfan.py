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
qianfan data source implementation including uploading / downloading
"""

import json
import os
import uuid
import zipfile
from typing import Any, Dict, Optional, Tuple

import dateutil.parser
import pyarrow

from qianfan.config import encoding, get_config
from qianfan.dataset.consts import (
    QianfanDatasetDownloadingCacheDir,
)
from qianfan.dataset.data_source.base import DataSource, FormatType
from qianfan.dataset.data_source.file import FileDataSource
from qianfan.dataset.data_source.utils import (
    _check_is_any_data_existed_in_dataset,
    _create_export_data_task_and_wait_for_success,
    _create_import_data_task_and_wait_for_success,
    _create_release_data_task_and_wait_for_success,
    _datetime_parse_hook,
    _download_file_from_url_streamly,
    _get_a_memory_mapped_pyarrow_table,
    _get_data_format_from_template_type,
    _get_latest_export_record,
    _get_qianfan_dataset_type_tuple,
    _read_all_file_content_in_an_folder,
    upload_data_from_bos_to_qianfan,
    zip_file_or_folder,
)
from qianfan.dataset.table import Table
from qianfan.errors import FileSizeOverflow, QianfanRequestError
from qianfan.resources import Data
from qianfan.resources.console.consts import (
    DataProjectType,
    DataSetType,
    DataStorageType,
    DataTemplateType,
)
from qianfan.utils import log_debug, log_error, log_info, log_warn
from qianfan.utils.bos_uploader import BosHelper
from qianfan.utils.pydantic import BaseModel, Field


class QianfanDataSource(DataSource, BaseModel):
    """Qianfan data source"""

    id: str
    group_id: str
    name: str
    set_type: DataSetType
    project_type: DataProjectType
    template_type: DataTemplateType
    version: int
    storage_type: DataStorageType
    storage_id: str
    storage_path: str
    storage_raw_path: Optional[str] = Field(default=None)
    storage_name: str
    storage_region: Optional[str] = Field(default=None)
    info: Dict[str, Any] = Field(default={})
    # 开关控制是否需要下载到本地进行后续处理。
    # 如果不需要，则创建一个千帆平台对应数据集的代理对象。
    # 这个参数现已废弃，为保证向前兼容性暂时保留，请勿使用
    download_when_init: Optional[bool] = Field(default=None)
    data_format_type: FormatType
    old_dataset_id: Optional[int] = None

    ak: Optional[str] = None
    sk: Optional[str] = None

    def _get_transmission_bos_info(
        self,
        sup_storage_id: str = "",
        sup_storage_path: str = "",
        sup_storage_region: str = "",
    ) -> Tuple[str, str, str]:
        """get bos info from arguments, attribute or global config"""
        if sup_storage_id and sup_storage_path and sup_storage_region:
            storage_id = sup_storage_id
            storage_path = sup_storage_path
            storage_region = sup_storage_region
        elif self.storage_type == DataStorageType.PrivateBos:
            storage_id = self.storage_id

            assert self.storage_raw_path
            storage_path = self.storage_raw_path

            assert self.storage_region
            storage_region = self.storage_region
        elif self.storage_type == DataStorageType.PublicBos:
            err_msg = "don't support upload dataset to dataset which use platform bos"
            log_error(err_msg)
            raise NotImplementedError()
        else:
            err_msg = "can't get storage info for uploading to qianfan"
            log_error(err_msg)
            raise ValueError(err_msg)

        # 此 path 必须以 / 结尾，为了防止用户没有加上，这里特判
        if storage_path[-1] != "/":
            storage_path += "/"

        return storage_id, storage_path, storage_region

    def _get_console_ak_and_sk(self) -> Tuple[str, str]:
        """get ak and sk from attribute or global config"""
        ak = self.ak if self.ak else get_config().ACCESS_KEY
        sk = self.sk if self.sk else get_config().SECRET_KEY
        if not ak:
            err_msg = "no ak was provided"
            log_error(err_msg)
            raise ValueError(log_error)
        if not sk:
            err_msg = "no sk was provided"
            log_error(err_msg)
            raise ValueError(err_msg)

        return ak, sk

    def save(
        self,
        table: Table,
        is_annotated: bool = False,
        does_release: bool = False,
        sup_storage_id: str = "",
        sup_storage_path: str = "",
        sup_storage_region: str = "",
        **kwargs: Any,
    ) -> bool:
        """
        Write data to qianfan
        Currently only support to write to
        user BOS storage

         Args:
            table (Table):
                data waiting to be uploaded.
            is_annotated (bool):
                has data been annotated, default to False
            does_release (bool):
                does release dataset
                after saving successfully,
                default to False
            sup_storage_id (Optional[str]):
                bos bucket name used for uploading,
                we recommend to use this parameter
                when your destination dataset on qianfan
                is stored in public BOS.
                Default to empty str
            sup_storage_path (Optional[str]):
                bos bucket file path used for uploading,
                we recommend to use this parameter
                when your destination dataset on qianfan
                is stored in public BOS.
                Default to empty str
            sup_storage_region (Optional[str]):
                bos bucket region used for uploading,
                we recommend to use this parameter
                when your destination dataset on qianfan
                is stored in public BOS.
                Default to empty str
            **kwargs (Any): optional arguments。

        Returns:
            bool: has data been uploaded successfully
        """
        # 如果是泛文本，则需要保存为压缩包格式
        should_save_as_zip_file = self.template_type == DataTemplateType.GenericText

        # 获取存储信息和鉴权信息
        storage_id, storage_path, storage_region = self._get_transmission_bos_info(
            sup_storage_id, sup_storage_path, sup_storage_region
        )
        ak, sk = self._get_console_ak_and_sk()

        # 构造本地和远端的路径
        if not should_save_as_zip_file:
            file_name = f"data_{uuid.uuid4()}.{self.format_type().value}"
            remote_file_path = f"{storage_path}{file_name}"
        # 因为泛文本需要打包成压缩包，所以单独处理
        else:
            file_name = f"data_{uuid.uuid4()}"
            remote_file_path = f"{storage_path}{file_name}.zip"

        # 如果数据集还是 grouped 格式，需要先转换为 packed
        if table.is_dataset_grouped() and not should_save_as_zip_file:
            table.pack()

        # 构造本地路径并且保存数据到缓存文件
        local_file_path = os.path.join(self._get_cache_folder_path(), file_name)
        FileDataSource(
            path=local_file_path,
            file_format=self.format_type(),
            save_as_folder=should_save_as_zip_file,
        ).save(
            table,
            use_qianfan_special_jsonl_format=not should_save_as_zip_file,
            **kwargs,
        )

        # 如果是泛文本还需要打压缩包
        if should_save_as_zip_file:
            local_file_path = zip_file_or_folder(local_file_path)

        log_info("start to upload data to user BOS")
        log_debug(
            f"bucket path: {remote_file_path} bucket name: {storage_id} bos region:"
            f" {storage_region}"
        )

        # 上传文件
        bos_helper = BosHelper(storage_region, ak, sk)

        log_info(f"upload dataset file {local_file_path} to {remote_file_path}")
        bos_helper.upload_file_to_bos(local_file_path, remote_file_path, storage_id)

        log_info("uploading data to user BOS finished")

        upload_data_from_bos_to_qianfan(
            bos_helper,
            should_save_as_zip_file,
            self.id,
            storage_id,
            remote_file_path,
            is_annotated,
        )

        if does_release:
            log_info("release after saving starts")
            return self.release_dataset(**kwargs)

        return True

    def _fetch_data_from_remote(self, zip_file_path: str, **kwargs: Any) -> Dict:
        """从远端发起数据导出任务，并且将导出的数据集保存在本地缓存文件中"""
        parser = dateutil.parser.parser()

        info = Data.get_dataset_info(self.id, **kwargs)["result"]["versionInfo"]
        log_info(f"get dataset info succeeded for dataset id {self.id}")
        # 如果用户没有导出过，或者最新一次的导出记录晚于更新时间，则重新导出数据集
        if (
            info["exportRecordCount"] == 0
            or parser.parse(info["modifyTime"])
            > _get_latest_export_record(self.id, **kwargs)[1]
        ):
            _create_export_data_task_and_wait_for_success(self.id, **kwargs)

        newest_record = _get_latest_export_record(self.id, **kwargs)[0]
        download_url = newest_record["downloadUrl"]

        # 流式下载到本地文件中
        _download_file_from_url_streamly(download_url, zip_file_path)

        log_info(f"download dataset zip to {zip_file_path} succeeded")
        return newest_record

    def _save_remote_into_file(
        self, content_path: str, bin_path: str, info_path: str, **kwargs: Any
    ) -> None:
        """将数据集从远端保存到本地"""
        info = self._fetch_data_from_remote(bin_path, **kwargs)
        with zipfile.ZipFile(bin_path) as zip_f:
            og_file_size: int = 0
            for file_info in zip_f.infolist():
                og_file_size += file_info.file_size

            # 检查下载下来的文件大小
            # 如果超过限制，则报错
            if og_file_size >= get_config().EXPORT_FILE_SIZE_LIMIT:
                error = FileSizeOverflow(
                    f"dataset file size is too big to unzip: {og_file_size}"
                )
                log_error(str(error))
                raise error

            # 解压到本地
            zip_f.extractall(content_path)

        log_info(f"unzip dataset to path {content_path} successfully")
        with open(info_path, mode="w", encoding=encoding()) as f:
            f.write(json.dumps(info, ensure_ascii=False))

        log_info(f"write dataset info to path {info_path} successfully")

    def _get_cache_folder_path(self) -> str:
        return os.path.join(
            QianfanDatasetDownloadingCacheDir,
            str(self.group_id),
            str(self.id),
            str(self.version),
        )

    def get_cache_content(self) -> str:
        return os.path.join(
            self._get_cache_folder_path(),
            "content",
        )

    def _get_and_update_dataset_cache(self, **kwargs: Any) -> pyarrow.Table:
        """从本地缓存中获取数据集，并且更新或者下载数据集"""

        # 检查目录，如果不存在目录则创建
        cache_dir = self._get_cache_folder_path()
        if not os.path.exists(cache_dir) or not os.path.isdir(cache_dir):
            os.makedirs(cache_dir)

        info_path = os.path.join(cache_dir, "info.json")
        bin_path = os.path.join(cache_dir, "bin.zip")
        content_path = os.path.join(cache_dir, "content")

        # 如果不存在缓存文件，则创建缓存文件
        if not os.path.exists(info_path) or not os.path.exists(content_path):
            log_info("no cache was found, download cache")
            self._save_remote_into_file(content_path, bin_path, info_path, **kwargs)

        # 尝试从本地缓存中读取数据
        try:
            with open(info_path, mode="r", encoding=encoding()) as f:
                dataset_info = json.load(f, object_hook=_datetime_parse_hook)

            # 获取最新的数据集信息
            qianfan_resp = Data.get_dataset_info(self.id, **kwargs)["result"][
                "versionInfo"
            ]

            # 并且判断数据集缓存是否有效
            parser = dateutil.parser.parser()
            if parser.parse(qianfan_resp["modifyTime"]) > parser.parse(
                dataset_info["finishTime"]
            ):
                # 如果无效，更新缓存
                log_info("dataset cache is outdated, update cache")
                self._save_remote_into_file(content_path, bin_path, info_path, **kwargs)
        except Exception as e:
            # 如果异常，则抛出，日后看下怎么加兜底逻辑
            log_error(f"an error occurred in fetch cache: {str(e)}")
            raise

        if os.path.isfile(content_path):
            return _get_a_memory_mapped_pyarrow_table(content_path, self.format_type())

        else:
            return _read_all_file_content_in_an_folder(content_path, self.format_type())

    def load(self, **kwargs: Any) -> Optional[pyarrow.Table]:
        """
        Get a pyarrow.Table from current DataSource object

        Args:
            **kwargs (Any): Arbitrary keyword arguments.

        Returns:
            Optional[pyarrow.Table]: A memory-mapped pyarrow.Table object or None
        """
        if self.download_when_init:
            return self.fetch(**kwargs)

        return None

    def fetch(self, **kwargs: Any) -> pyarrow.Table:
        """
        Read data from qianfan.

        Args:
            **kwargs (Any): Arbitrary keyword arguments.

        Returns:
            pyarrow.Table: table retrieved from file
        """
        if self.ak and self.sk:
            kwargs["ak"] = self.ak
            kwargs["sk"] = self.sk
        if not _check_is_any_data_existed_in_dataset(self.id, **kwargs):
            error = LookupError("no data exists in dataset")
            log_error(str(error))
            raise error

        return self._get_and_update_dataset_cache(**kwargs)

    def format_type(self) -> FormatType:
        """
        Get format type binding to qianfan data source

        Returns:
            FormatType: format type binding to qianfan data source
        """
        assert self.data_format_type
        return self.data_format_type

    def set_format_type(self, format_type: FormatType) -> None:
        """
        Set format type binding to qianfan data source
        Not available

        TextOnly -> Jsonl
        MultiModel -> Json
        """
        # 不支持设置，和数据集类型绑定
        # 文本都是 jsonl
        # 文生图都是 json
        raise NotImplementedError()

    @classmethod
    def _create_bare_dataset(
        cls,
        name: str,
        template_type: DataTemplateType,
        storage_type: DataStorageType = DataStorageType.PublicBos,
        storage_id: Optional[str] = None,
        storage_path: Optional[str] = None,
        addition_info: Optional[Dict[str, Any]] = None,
        ak: Optional[str] = None,
        sk: Optional[str] = None,
        **kwargs: Any,
    ) -> "QianfanDataSource":
        log_info("start to create dataset on qianfan")
        project_type, set_type = _get_qianfan_dataset_type_tuple(template_type)

        # 发起创建数据集的请求
        qianfan_resp = Data.create_bare_dataset(
            name,
            set_type,
            project_type,
            template_type,
            storage_type,
            storage_id,
            storage_path,
            ak=ak,
            sk=sk,
            **kwargs,
        )["result"]

        log_debug(f"create qianfan dataset response: {qianfan_resp}")
        log_info("create dataset on qianfan successfully")
        # 构造对象
        source = cls(
            id=qianfan_resp["datasetId"],
            group_id=qianfan_resp["groupPK"],
            name=name,
            version=qianfan_resp["versionId"],
            set_type=set_type,
            project_type=project_type,
            template_type=template_type,
            storage_type=storage_type,
            storage_id=qianfan_resp["storageInfo"]["storageId"],
            storage_path=qianfan_resp["storageInfo"]["storagePath"],
            storage_name=qianfan_resp["storageInfo"]["storageName"],
            info=(
                {**qianfan_resp, **addition_info} if addition_info else {**qianfan_resp}
            ),
            data_format_type=_get_data_format_from_template_type(template_type),
            old_dataset_id=qianfan_resp.get("id"),
            ak=ak,
            sk=sk,
        )

        # 如果是私有的 BOS，还需要额外填充返回的 region 信息
        if storage_type == DataStorageType.PrivateBos:
            source.storage_region = qianfan_resp["storageInfo"]["region"]
            source.storage_raw_path = qianfan_resp["storageInfo"]["rawStoragePath"]

        return source

    @classmethod
    def create_bare_dataset(
        cls,
        name: str,
        template_type: DataTemplateType,
        storage_type: DataStorageType = DataStorageType.PublicBos,
        storage_id: Optional[str] = None,
        storage_path: Optional[str] = None,
        addition_info: Optional[Dict[str, Any]] = None,
        ak: Optional[str] = None,
        sk: Optional[str] = None,
        **kwargs: Any,
    ) -> "QianfanDataSource":
        """
        create bare dataset on qianfan as data source, which is empty
        Args:
            name (str):
                dataset name you want
            template_type (DataTemplateType):
                template type applying to data set
            storage_type (Optional[DataStorageType]):
                data storage type used to store your data, default to PublicBos
            storage_id (Optional[str]): private BOS bucket name，
                needed when storage_type is PrivateBos, default to None
            storage_path (Optional[str]): private BOS file path，
                needed when storage_type is PrivateBos, default to None
            addition_info (Optional[Dict[str, Any]]):
                additional info you want to have，default to None
            ak (Optional[str]):
                console ak related to your dataset and bos，default to None
            sk (Optional[str]):
                console sk related to your dataset and bos，default to None
            kwargs (Any): other arguments

        Returns:
            QianfanDataSource: A datasource represents your dataset on Qianfan
        """

        if storage_type == DataStorageType.PrivateBos and not (
            storage_id and storage_path
        ):
            error = ValueError("storage_id or storage_path missing")
            log_error(str(error))
            raise error

        return cls._create_bare_dataset(
            name,
            template_type,
            storage_type,
            storage_id,
            storage_path,
            addition_info,
            ak,
            sk,
            **kwargs,
        )

    @classmethod
    def create_from_bos_file(
        cls,
        name: str,
        template_type: DataTemplateType,
        storage_id: str,
        storage_path: str,
        file_name: str,
        is_data_annotated: bool,
        storage_type: DataStorageType = DataStorageType.PrivateBos,
        addition_info: Optional[Dict[str, Any]] = None,
        ak: Optional[str] = None,
        sk: Optional[str] = None,
        is_download_to_local: Optional[bool] = None,
        **kwargs: Any,
    ) -> "QianfanDataSource":
        """
        create a dataset on qianfan as data source,
        which will import data from specific bos
        Args:
            name (str):
                dataset name you want
            template_type (DataTemplateType):
                template type applying to data set
            storage_id (str):
                private BOS bucket name
            storage_path (str):
                private BOS file path
            file_name (str):
                file need to upload
            is_data_annotated (bool):
                is data in bos annotated
            storage_type (Optional[DataStorageType]):
                data storage type used to store your data, default to PrivateBos
            addition_info (Optional[Dict[str, Any]]):
                additional info you want to have，default to None
            ak (Optional[str]):
                console ak related to your dataset and bos，default to None
            sk (Optional[str]):
                console sk related to your dataset and bos，default to None
            is_download_to_local (Optional[bool]):
                This parameter has been set as deprecated.
                does dataset download file when initialize object，default to None
            kwargs (Any): other arguments

        Returns:
            QianfanDataSource: A datasource represents your dataset on Qianfan
        """

        log_info("start to create dataset on qianfan from bos")
        storage_info_for_create: Dict[str, Any] = {}

        if storage_type == DataStorageType.PrivateBos:
            storage_info_for_create = {
                "storage_id": storage_id,
                "storage_path": storage_path,
            }

        log_debug(f"storage_info: {storage_info_for_create}")
        log_info("start to create bare dataset")

        source = cls._create_bare_dataset(
            name,
            template_type,
            storage_type,
            addition_info=addition_info,
            ak=ak,
            sk=sk,
            **storage_info_for_create,
            **kwargs,
        )

        log_info("start to import data in bos")
        if not _create_import_data_task_and_wait_for_success(
            source.id, is_data_annotated, f"{storage_id}{storage_path}{file_name}"
        ):
            err_msg = "failed to create dataset from bos file"
            log_error(err_msg)
            raise QianfanRequestError(err_msg)

        if is_download_to_local is not None:
            log_warn('parameter "is_download_to_local" has been set as deprecated')
            source.download_when_init = is_download_to_local

        return source

    @classmethod
    def get_existed_dataset(
        cls,
        dataset_id: str,
        is_download_to_local: Optional[bool] = None,
        ak: Optional[str] = None,
        sk: Optional[str] = None,
        **kwargs: Any,
    ) -> "QianfanDataSource":
        """
        Load a dataset from qianfan as data source

        Args:
            dataset_id (str):
                dataset id on Qianfan, show as "数据集版本 ID"
            is_download_to_local (Optional[bool]):
                This parameter has been set as deprecated.
                does dataset download file when initialize object，default to None
            ak (Optional[str]):
                console ak related to your dataset and bos，default to None
            sk (Optional[str]):
                console sk related to your dataset and bos，default to None
            kwargs (Any): other arguments

        Returns:
            QianfanDataSource: A datasource represents your dataset on Qianfan
        """

        # 获取数据集信息
        qianfan_resp = Data.get_dataset_info(dataset_id, ak=ak, sk=sk, **kwargs)[
            "result"
        ]

        # 校验和推断各类对象

        set_type = DataSetType(qianfan_resp["versionInfo"]["dataType"])
        if not set_type:
            error = ValueError(
                f'qianfan set type {qianfan_resp["versionInfo"]["dataType"]} not found'
            )
            log_error(str(error))
            raise error

        project_type = DataProjectType(qianfan_resp["versionInfo"]["projectType"])
        if not project_type:
            error = ValueError(
                f'qianfan project type {qianfan_resp["versionInfo"]["projectType"]} not'
                " found"
            )
            log_error(str(error))
            raise error

        template_type = DataTemplateType(qianfan_resp["versionInfo"]["templateType"])
        if not template_type:
            error = ValueError(
                "qianfan template type"
                f" {qianfan_resp['versionInfo']['templateType']} not found"
            )
            log_error(str(error))
            raise error

        storage_type = DataStorageType(qianfan_resp["versionInfo"]["storageType"])
        if not storage_type:
            error = ValueError(
                f'qianfan storage type {qianfan_resp["versionInfo"]["storageType"]} not'
                " found"
            )
            log_error(str(error))
            raise error

        # 创建对象
        dataset = cls(
            id=qianfan_resp["versionInfo"]["datasetPK"],
            group_id=qianfan_resp["groupPK"],
            name=qianfan_resp["name"],
            version=qianfan_resp["versionInfo"]["versionId"],
            set_type=set_type,
            project_type=project_type,
            template_type=template_type,
            storage_type=storage_type,
            storage_id=qianfan_resp["versionInfo"]["storage"]["storageId"],
            storage_path=qianfan_resp["versionInfo"]["storage"]["storagePath"],
            storage_raw_path=qianfan_resp["versionInfo"]["storage"]["rawStoragePath"],
            storage_name=qianfan_resp["versionInfo"]["storage"]["storageName"],
            storage_region=qianfan_resp["versionInfo"]["storage"]["region"],
            download_when_init=is_download_to_local,
            info={**qianfan_resp},
            data_format_type=_get_data_format_from_template_type(template_type),
            old_dataset_id=qianfan_resp["versionInfo"].get("datasetId"),
            ak=ak,
            sk=sk,
        )

        if is_download_to_local is not None:
            log_warn('parameter "is_download_to_local" has been set as deprecated')

        return dataset

    def release_dataset(self, **kwargs: Any) -> bool:
        """
        make a dataset released

        Returns:
            bool: Whether releasing succeeded
        """
        return _create_release_data_task_and_wait_for_success(self.id, **kwargs)
