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
data source which is related to download/upload
"""

import datetime
import json
import os.path
import uuid
import zipfile
from abc import ABC, abstractmethod
from enum import Enum
from time import sleep
from typing import Any, Dict, List, Optional, Tuple, Union

import dateutil.parser
import requests
from pydantic import BaseModel, Field, model_validator

from qianfan.config import get_config
from qianfan.dataset.consts import QianfanDatasetLocalCacheDir
from qianfan.errors import FileSizeOverflow, QianfanRequestError
from qianfan.resources.console.consts import (
    DataExportDestinationType,
    DataExportStatus,
    DataImportStatus,
    DataProjectType,
    DataReleaseStatus,
    DataSetType,
    DataSourceType,
    DataStorageType,
    DataTemplateType,
)
from qianfan.resources.console.data import Data
from qianfan.utils.bos_uploader import (
    generate_bos_file_path,
    get_bos_file_shared_url,
    upload_content_to_bos,
    upload_file_to_bos,
)
from qianfan.utils.logging import log_debug, log_error, log_info, log_warn


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


# 目前第一期主要支持本地调用
# 且目前只支持读单个文件，文件夹兼容稍后
class FileDataSource(DataSource, BaseModel):
    """file data source"""

    path: str
    file_format: Optional[FormatType] = Field(default=None)

    def save(self, data: str, **kwargs: Any) -> bool:
        """
        Write data to file。

        Args:
            data (str): data waiting to be written。
            **kwargs (Any): optional arguments。

        Returns:
            bool: has data been written successfully
        """
        if os.path.isdir(self.path):
            file_path = os.path.join(
                self.path, f"data_{uuid.uuid4()}.{self.format_type().value}"
            )
        else:
            file_path = self.path
        with open(file_path, mode="w") as file:
            file.write(data)
        return True

    async def asave(self, data: str, **kwargs: Any) -> bool:
        """
        Asynchronously Write data to file。
        Not available currently

        Args:
            data (str): data waiting to be written。
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
        if not os.path.exists(self.path):
            raise ValueError("file path not found")
        if os.path.isdir(self.path):
            ret_list: List[str] = []

            # 不保证文件读取的顺序性
            for root, dirs, files in os.walk(self.path):
                for file_name in files:
                    if not file_name.endswith(self.format_type().value):
                        continue

                    file_path = os.path.join(root, file_name)
                    with open(file_path, mode="r") as f:
                        ret_list.append(f.read())

            return ret_list
        else:
            with open(self.path, mode="r") as file:
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

    @model_validator(mode="after")
    def _format_check(self) -> "FileDataSource":
        if self.file_format:
            return self

        try:
            index = self.path.rfind(".")
            # 读文件夹或查询不到的情况下默认使用纯文本格式
            if os.path.isdir(self.path) or index == -1:
                log_warn(f"use default format type {FormatType.Text}")
                self.file_format = FormatType.Text
                return self
            suffix = self.path[index + 1 :]
            for t in FormatType:
                if t.value == suffix:
                    self.file_format = t
                    log_info(f"use format type {t}")
                    return self
            raise ValueError(f"cannot match proper format type for {suffix}")
        except Exception as e:
            log_error(str(e))
            raise e


# 使用 DataTemplateType 来推断配对的 FormatType
def _get_data_format_from_template_type(template_type: DataTemplateType) -> FormatType:
    if template_type in [
        DataTemplateType.NonSortedConversation,
        DataTemplateType.SortedConversation,
        DataTemplateType.QuerySet,
    ]:
        return FormatType.Jsonl
    elif template_type == DataTemplateType.GenericText:
        return FormatType.Text
    return FormatType.Json


def _create_import_data_task_and_wait_for_success(
    dataset_id: int,
    is_annotated: bool,
    file_path: str,
    source_type: DataSourceType = DataSourceType.PrivateBos,
) -> bool:
    Data.create_data_import_task(
        dataset_id,
        is_annotated,
        source_type,
        file_path,
    )

    log_info("successfully create importing task")
    while True:
        sleep(get_config().IMPORT_STATUS_POLLING_INTERVAL)
        log_info("polling import task status")
        qianfan_resp = Data.get_dataset_info(dataset_id)["result"]["versionInfo"]
        status = qianfan_resp["importStatus"]
        if status in [
            DataImportStatus.NotStarted.value,
            DataImportStatus.Running.value,
        ]:
            log_info(f"import status: {status}, keep polling")
            continue
        elif status == DataImportStatus.Finished.value:
            log_info("import succeed")
            return True
        else:
            log_error(f"import failed with status {status}")
            return False


# 千帆平台的数据源
class QianfanDataSource(DataSource, BaseModel):
    """Qianfan data source"""

    id: int
    group_id: int
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
    download_when_init: bool = Field(default=False)
    data_format_type: FormatType

    ak: Optional[str] = None
    sk: Optional[str] = None

    @classmethod
    def _get_qianfan_dataset_type_tuple(
        cls, template_type: DataTemplateType
    ) -> Tuple[DataProjectType, DataSetType]:
        for t in DataProjectType:
            # DataProjectType 是匹配的 DataTemplateType 的前缀
            # 具体来说，DataTemplateType 在整除 100 后得到的整数
            # 即是 DataProjectType
            # 此处通过整数除法计算前缀
            if template_type.value // t.value == 100:
                if template_type == DataTemplateType.Text2Image:
                    log_debug(
                        f"inferred project type: {t}, set type:"
                        f" {DataSetType.MultiModel}"
                    )
                    return t, DataSetType.MultiModel
                else:
                    log_debug(
                        f"inferred project type: {t}, set type: {DataSetType.TextOnly}"
                    )
                    return t, DataSetType.TextOnly
        error = ValueError(
            f"no project type and set type found matching with {template_type}"
        )
        log_error(error)
        raise error

    def save(
        self,
        data: Optional[str] = None,
        zip_file_path: Optional[str] = None,
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
            data (str): data waiting to be uploaded. Default to None
            zip_file_path (Optional[str]):
                zip file path which contains data files, default to None.
            is_annotated (bool): has data been annotated, default to False
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
        if data and zip_file_path:
            err_msg = "can't set 'data' and 'zip_file_path' simultaneously"
            log_error(err_msg)
            raise ValueError(err_msg)

        if not data and not zip_file_path:
            err_msg = "must set either 'data' or 'zip_file_path'"
            log_error(err_msg)
            raise ValueError(err_msg)

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

        ak = self.ak if self.ak else get_config().ACCESS_KEY
        sk = self.sk if self.sk else get_config().SECRET_KEY
        if not ak:
            log_warn("no ak was provided when upload data to user BOS")
            return False
        if not sk:
            log_warn("no sk was provided when upload data to user BOS")
            return False

        if not storage_region:
            log_warn("no region was provided when upload data to user BOS")
            return False

        if not zip_file_path:
            suffix = "jsonl" if self.format_type() != FormatType.Text else "txt"
            file_path = f"{storage_path}data_{uuid.uuid4()}.{suffix}"
        else:
            file_path = f"{storage_path}{os.path.split(zip_file_path)[-1]}"

        log_info("start to upload data to user BOS")
        log_debug(
            f"bucket path: {file_path} bucket name: {storage_id} bos region:"
            f" {storage_region}"
        )

        if data:
            log_info("upload dataset as string")
            upload_content_to_bos(
                data,
                file_path,
                storage_id,
                storage_region,
                ak,
                sk,
            )
        elif zip_file_path:
            log_info("upload dataset as zip")
            upload_file_to_bos(
                zip_file_path,
                file_path,
                storage_id,
                storage_region,
                ak,
                sk,
            )
        else:
            err_msg = "unexpected conditional branch error when upload dataset to bos"
            log_error(err_msg)
            raise Exception(err_msg)

        log_info("uploading data to user BOS finished")

        if not zip_file_path:
            complete_file_path = generate_bos_file_path(storage_id, file_path)
            if not _create_import_data_task_and_wait_for_success(
                self.id, is_annotated, complete_file_path
            ):
                log_warn("import data from bos file failed")
                return False
        else:
            shared_str = get_bos_file_shared_url(
                file_path, storage_id, storage_region, ak, sk
            )
            log_info(f"get shared file url: {shared_str}")
            if not _create_import_data_task_and_wait_for_success(
                self.id, is_annotated, shared_str, DataSourceType.SharedZipUrl
            ):
                log_warn("import data from shared zip url failed")
                return False

        if does_release:
            log_info("release after saving starts")
            return self.release_dataset(**kwargs)
        return True

    async def asave(self, data: str, is_annotated: bool = False, **kwargs: Any) -> bool:
        """
        Asynchronously write data to qianfan
        currently only support to write to
        user BOS storage

        Not available currently

         Args:
            data (str): data waiting to be uploaded。
            is_annotated (bool): has data been annotated
            **kwargs (Any): optional arguments。

        Returns:
            bool: has data been uploaded successfully
        """
        raise NotImplementedError()

    def _get_latest_export_record(
        self, **kwargs: Any
    ) -> Tuple[Dict, datetime.datetime]:
        """从平台获取最新的数据集导出记录信息，以及它的导出时间"""
        parser = dateutil.parser.parser()
        export_records = Data.get_dataset_export_records(self.id, **kwargs)["result"]
        log_info(f"get export records succeeded for dataset id {self.id}")
        newest_record_index, latest_record_time = 0, datetime.datetime(1970, 1, 1)

        for index in range(len(export_records)):
            record = export_records[index]
            try:
                date = parser.parse(record["finishTime"])
                if date > latest_record_time:
                    newest_record_index = index
                    latest_record_time = date
            except Exception as e:
                log_warn(
                    f"an exception occurred when fetch export records info: {str(e)}"
                )
                continue

        log_info(
            f"latest dataset with time{latest_record_time} "
            f"for dataset id {export_records[newest_record_index]['id']}"
        )
        return export_records[newest_record_index], latest_record_time

    def _fetch_data_from_remote(self, zip_file_path: str, **kwargs: Any) -> Dict:
        """从远端发起数据导出任务，并且将导出的数据集保存在本地缓存文件中"""
        parser = dateutil.parser.parser()

        info = Data.get_dataset_info(self.id, **kwargs)["result"]["versionInfo"]
        log_info(f"get dataset info succeeded for dataset id {self.id}")
        # 如果用户没有导出过，或者最新一次的导出记录晚于更新时间，则重新导出数据集
        if (
            info["exportRecordCount"] == 0
            or parser.parse(info["modifyTime"])
            > self._get_latest_export_record(**kwargs)[1]
        ):
            log_info("start to export dataset")
            Data.create_dataset_export_task(
                self.id, DataExportDestinationType.PlatformBos, **kwargs
            )
            log_info("create dataset export task successfully")

            # 轮巡导出状态
            while True:
                sleep(get_config().EXPORT_STATUS_POLLING_INTERVAL)
                log_info("polling export task status")
                info = Data.get_dataset_info(self.id, **kwargs)["result"]["versionInfo"]
                status = info["exportStatus"]

                if status == DataExportStatus.Finished.value:
                    log_info("export succeed")
                    break
                elif status == DataExportStatus.Running.value:
                    log_info(f"export status: {status}, keep polling")
                    continue
                elif status == DataExportStatus.Failed.value:
                    error = QianfanRequestError(
                        f"export dataset failed with status {status}"
                    )
                    log_error(str(error))
                    raise error

        newest_record = self._get_latest_export_record(**kwargs)[0]
        download_url = newest_record["downloadUrl"]

        # 流式下载到本地文件中
        log_info(f"start to download dataset zip from url {download_url}")
        try:
            resp = requests.get(download_url, stream=True)
            with open(zip_file_path, "wb") as f:
                for chuck in resp.iter_content(10240):
                    f.write(chuck)
            resp.close()
        except Exception as e:
            log_error(f"exception occurred during download {str(e)}")
            raise e

        if resp.status_code != 200:
            http_error = Exception(
                "download dataset zip from remote failed with http status code"
                f" {resp.status_code}"
            )
            log_error(str(http_error))
            raise http_error

        log_info(f"download dataset zip to {zip_file_path} succeeded")
        return newest_record

    def _save_remote_into_file(
        self, content_path: str, bin_path: str, info_path: str, **kwargs: Any
    ) -> None:
        """将数据集从远端保存到本地"""
        info = self._fetch_data_from_remote(bin_path, **kwargs)
        with zipfile.ZipFile(bin_path) as zip_f:
            json_file_name = zip_f.namelist()[0]

            # 检查下载下来的文件大小
            # 如果超过限制，则报错
            if (
                zip_f.getinfo(json_file_name).file_size
                >= get_config().EXPORT_FILE_SIZE_LIMIT
            ):
                error = FileSizeOverflow(
                    "dataset file size is too big to unzip:"
                    f" {zip_f.getinfo(json_file_name).file_size}"
                )
                log_error(str(error))
                raise error

            # 解压到本地
            zip_f.extractall(content_path)

        log_info(f"unzip dataset to path {content_path} successfully")
        with open(info_path, mode="w") as f:
            f.write(json.dumps(info))

        log_info(f"write dataset info to path {info_path} successfully")

    def _get_and_update_dataset_cache(self, **kwargs: Any) -> Union[str, List[str]]:
        """从本地缓存中获取数据集，并且更新或者下载数据集"""

        # 检查目录，如果不存在目录则创建
        cache_dir = os.path.join(
            QianfanDatasetLocalCacheDir,
            str(self.group_id),
            str(self.id),
            str(self.version),
        )
        if not os.path.exists(cache_dir) or not os.path.isdir(cache_dir):
            os.makedirs(cache_dir)

        info_path = os.path.join(cache_dir, "info.json")
        bin_path = os.path.join(cache_dir, "bin.zip")
        content_path = os.path.join(cache_dir, "content")

        # 如果不存在缓存文件，则创建缓存文件
        if not os.path.exists(info_path) or not os.path.exists(content_path):
            log_info("no cache was found, download cache")
            self._save_remote_into_file(content_path, bin_path, info_path, **kwargs)

        # json 解析钩子，将值中的时间戳字符串解析为 datetime 对象
        def _datetime_parse_hook(obj: Any) -> Union[datetime.datetime, str]:
            if isinstance(obj, str):
                try:
                    return dateutil.parser.parser().parse(timestr=obj)
                except Exception:
                    return obj
            return obj

        # 尝试从本地缓存中读取数据
        try:
            with open(info_path, mode="r") as f:
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
            with open(content_path, mode="r") as f:
                self.download_when_init = True
                return f.read()

        else:
            ret_list: List[str] = []
            for root, dirs, files in os.walk(content_path):
                for file_name in files:
                    file_path = os.path.join(root, file_name)
                    with open(file_path, mode="r") as f:
                        ret_list.append(f.read())

            self.download_when_init = True
            return ret_list

    def _check_is_any_data_existed_in_dataset(self, **kwargs: Any) -> bool:
        """检查远端数据集是否为空"""

        qianfan_resp = Data.get_dataset_info(self.id, **kwargs)["result"]["versionInfo"]
        return qianfan_resp["entityCount"] != 0

    def fetch(self, **kwargs: Any) -> Union[str, List[str]]:
        """
        Read data from qianfan or local cache。

        Args:
            **kwargs (Any): Arbitrary keyword arguments.

        Returns:
            Union[str, List[str]]: content retrieved from data source
        """
        if self.ak and self.sk:
            kwargs["ak"] = self.ak
            kwargs["sk"] = self.sk
        if not self._check_is_any_data_existed_in_dataset(**kwargs):
            error = LookupError("no data exists in dataset")
            log_error(str(error))
            raise error

        return self._get_and_update_dataset_cache(**kwargs)

    async def afetch(self, **kwargs: Any) -> Union[str, List[str]]:
        """
        Asynchronously read data from qianfan or local cache。
        Not available currently

        Args:
            **kwargs (Any): Arbitrary keyword arguments.

        Returns:
            Union[str, List[str]]: content retrieved from data source
        """
        raise NotImplementedError()

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
        project_type, set_type = cls._get_qianfan_dataset_type_tuple(template_type)

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
            id=qianfan_resp["id"],
            group_id=qianfan_resp["groupId"],
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
            name (str): dataset name you want
            template_type (DataTemplateType): template type applying to data set
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
        is_download_to_local: bool = True,
        **kwargs: Any,
    ) -> "QianfanDataSource":
        """
        create a dataset on qianfan as data source,
        which will import data from specific bos
        Args:
            name (str): dataset name you want
            template_type (DataTemplateType): template type applying to data set
            storage_id (str): private BOS bucket name
            storage_path (str): private BOS file path
            file_name (str): file need to upload
            is_data_annotated (bool): is data in bos annotated
            storage_type (Optional[DataStorageType]):
                data storage type used to store your data, default to PrivateBos
            addition_info (Optional[Dict[str, Any]]):
                additional info you want to have，default to None
            ak (Optional[str]):
                console ak related to your dataset and bos，default to None
            sk (Optional[str]):
                console sk related to your dataset and bos，default to None
            is_download_to_local (bool):
                does dataset download file when initialize object，default to True
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

        if is_download_to_local:
            log_info("start to fetch dataset cache because is_download_to_local is set")
            source.fetch(**kwargs)

        return source

    @classmethod
    def get_existed_dataset(
        cls,
        dataset_id: int,
        is_download_to_local: bool = True,
        ak: Optional[str] = None,
        sk: Optional[str] = None,
        **kwargs: Any,
    ) -> "QianfanDataSource":
        """
        Load a dataset from qianfan as data source

        Args:
            dataset_id (int): dataset id on Qianfan, show as "数据集版本 ID"
            is_download_to_local (bool):
                does dataset download file when initialize object，default to True
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
            id=qianfan_resp["versionInfo"]["datasetId"],
            group_id=qianfan_resp["versionInfo"]["groupId"],
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
            ak=ak,
            sk=sk,
        )

        if is_download_to_local:
            log_info("start to fetch dataset cache because is_download_to_local is set")
            dataset.fetch(**kwargs)

        return dataset

    def release_dataset(self, **kwargs: Any) -> bool:
        """
        make a dataset released

        Returns:
            bool: Whether releasing succeeded
        """
        info = Data.get_dataset_info(self.id, **kwargs)["result"]["versionInfo"]
        status = info["releaseStatus"]
        if status == DataReleaseStatus.Finished:
            return True
        Data.release_dataset(self.id, **kwargs)
        while True:
            sleep(get_config().RELEASE_STATUS_POLLING_INTERVAL)
            info = Data.get_dataset_info(self.id)["result"]["versionInfo"]
            status = info["releaseStatus"]
            if status == DataReleaseStatus.Running:
                log_info("data releasing, keep rolling")
                continue
            elif status == DataReleaseStatus.Failed:
                message = (
                    f"data releasing failed with error code {info['releaseErrCode']}"
                )
                log_error(message)
                return False
            else:
                log_info("data releasing succeeded")
                return True
