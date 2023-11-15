import datetime
import io
import json
import os.path
import shutil
import zipfile
from abc import ABC, abstractmethod
from enum import Enum
from time import sleep
from typing import Any, Dict, Optional, Tuple, Union

import dateutil.parser
import requests
from pydantic import BaseModel, Field, model_validator

from qianfan.config import get_config
from qianfan.framework.dataset.consts import QianfanDatasetLocalCacheDir
from qianfan.resources.console.consts import (
    DataExportDestinationType,
    DataProjectType,
    DataSetType,
    DataStorageType,
    DataTemplateType, DataSourceType,
)
from qianfan.resources.console.data import Data
from qianfan.utils.bos_uploader import upload_content_to_bos


class FormatType(Enum):
    """数据源格式类型枚举"""

    Json = "json"
    Jsonl = "jsonl"
    Csv = "csv"
    # 无格式导出，一行就是一条数据，类似 Jsonl，但是非格式化
    Text = "txt"


class DataSource(ABC):
    @abstractmethod
    def save(self, data: str, **kwargs: Any) -> bool:
        """将数据导出到数据源中，返回导入成功或失败"""

    @abstractmethod
    async def asave(self, data: str, **kwargs: Any) -> bool:
        """异步导出，看情况实现"""

    @abstractmethod
    def fetch(self, **kwargs: Any) -> str:
        """从数据源中获取数据"""

    @abstractmethod
    async def afetch(self, **kwargs: Any) -> str:
        """从数据源中异步获取数据，看情况实现"""

    @abstractmethod
    def format_type(self) -> FormatType:
        """获取数据源绑定的数据格式"""

    @abstractmethod
    def set_format_type(self, format_type: FormatType) -> None:
        """设置数据源绑定的数据格式"""


# 目前第一期主要支持本地调用
# 且目前只支持读单个文件，文件夹兼容稍后
class FileDataSource(DataSource, BaseModel):
    path: str
    file_format: Optional[FormatType] = Field(default=None)

    def save(self, data: str, **kwargs: Any) -> bool:
        with open(self.path, mode="w") as file:
            file.write(data)
        return True

    async def asave(self, data: str, **kwargs: Any) -> bool:
        raise NotImplementedError()

    def fetch(self, **kwargs: Any) -> str:
        with open(self.path, mode="r") as file:
            return file.read()

    async def afetch(self, **kwargs: Any) -> str:
        raise NotImplementedError()

    def format_type(self) -> FormatType:
        assert self.file_format
        return self.file_format

    def set_format_type(self, format_type: FormatType) -> None:
        self.file_format = format_type

    @model_validator(mode="after")
    def _format_check(self) -> "FileDataSource":
        if not self.path:
            raise ValueError("file path cannot be empty")
        if os.path.isdir(self.path):
            raise ValueError("cannot read from folder")
        if self.file_format:
            return self
        index = self.path.rfind(".")
        # 查询不到的情况下默认使用纯文本格式
        if index == -1:
            self.file_format = FormatType.Text
            return self
        suffix = self.path[index + 1 :]
        for t in FormatType:
            if t.value == suffix:
                self.file_format = t
                return self
        raise ValueError(f"cannot match proper format type for {suffix}")


def _get_data_format_from_template_type(template_type: DataTemplateType):
    if template_type in [DataTemplateType.NonSortedConversation, DataTemplateType.SortedConversation, DataTemplateType.QuerySet]:
        return FormatType.Jsonl
    # 有待商榷
    elif template_type == DataTemplateType.GenericText:
        return FormatType.Text
    return FormatType.Json


# 千帆平台的数据源
class QianfanDataSource(DataSource, BaseModel):
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
    storage_name: str
    storage_region: str
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
            if template_type.value // t.value == 100:
                if template_type == DataTemplateType.Text2Image:
                    return t, DataSetType.MultiModel
                else:
                    return t, DataSetType.TextOnly
        raise ValueError(
            f"no project type and set type found matching with {template_type}"
        )

    _ImportStatusMap = {
        "waiting": 0,
        "exporting": 1,
        "complete": 2,
        "failed": 3,
        "interpreted": 4,
    }

    def save(self, data: str, **kwargs: Any) -> bool:
        if self.storage_type == DataStorageType.PublicBos:
            raise NotImplementedError()
        elif self.storage_type == DataStorageType.PrivateBos:
            # 只支持除泛文本以外的文本上传，文生图需要后续再细化。
            file_path = f"{self.storage_path}/data.jsonl"
            upload_content_to_bos(
                data,
                file_path,
                self.storage_id,
                self.storage_region,
                self.ak if self.ak else get_config().ACCESS_KEY,
                self.sk if self.sk else get_config().SECRET_KEY,
            )
            is_annotated = kwargs["is_annotated"]
            Data.create_data_import_task(self.id, is_annotated, DataSourceType.PrivateBos, file_path)
            while True:
                sleep(2)
                qianfan_resp = Data.get_dataset_info(self.id)['result']['versionInfo']
                status = qianfan_resp['importStatus']
                if status in [self._ImportStatusMap['waiting'], self._ImportStatusMap['exporting']]:
                    return True
                elif status == self._ImportStatusMap['complete']:
                    continue
                else:
                    return False

    async def asave(self, data: str, **kwargs: Any) -> bool:
        # 同 save
        raise NotImplementedError()

    _ExportStatusMap = {
        "exporting": 1,
        "complete": 2,
        "failed": 3,
    }

    def _get_latest_export_record(
        self, **kwargs: Any
    ) -> Tuple[Dict, datetime.datetime]:
        parser = dateutil.parser.parser()
        export_records = Data.get_dataset_export_records(self.id, **kwargs)["result"]
        newest_record_index, latest_record_time = 0, datetime.datetime(1970, 1, 1)

        for index in range(len(export_records)):
            record = export_records[index]
            try:
                date = parser.parse(record["finishTime"])
                if date > latest_record_time:
                    newest_record_index = index
                    latest_record_time = date
            except Exception:
                continue

        return export_records[newest_record_index], latest_record_time

    def _fetch_data_from_remote(self, **kwargs: Any) -> Tuple[bytes, Dict]:
        parser = dateutil.parser.parser()

        info = Data.get_dataset_info(self.id, **kwargs)["result"]["versionInfo"]
        # 如果用户没有导出过，或者最新一次的导出记录晚于更新时间，则重新导出数据集
        if (
            info["exportRecordCount"] == 0
            or parser.parse(info["modifyTime"])
            > self._get_latest_export_record(**kwargs)[1]
        ):
            print("开始导出数据集")
            # TODO 支持导出到用户 BOS
            Data.create_dataset_export_task(
                self.id, DataExportDestinationType.PlatformBos, **kwargs
            )
            while True:
                sleep(2)
                info = Data.get_dataset_info(self.id, **kwargs)["result"]["versionInfo"]
                status = info["exportStatus"]

                if status == self._ExportStatusMap["complete"]:
                    break
                elif status == self._ExportStatusMap["exporting"]:
                    continue
                elif status == self._ExportStatusMap["failed"]:
                    raise self.QianfanRequestError("export dataset failed")

        print("开始下载数据集")
        newest_record = self._get_latest_export_record(**kwargs)[0]
        download_url = newest_record["downloadUrl"]
        resp = requests.get(download_url)
        if resp.status_code != 200:
            raise Exception(
                "download dataset from remote failed with http status code"
                f" {resp.status_code}"
            )
        return resp.content, newest_record

    def _save_remote_into_file(
        self, bin_path: str, info_path: str, **kwargs: Any
    ) -> None:
        dataset_bin, info = self._fetch_data_from_remote(**kwargs)
        with zipfile.ZipFile(io.BytesIO(dataset_bin)) as zip_f:
            json_file_name = zip_f.namelist()[0]
            zip_f.extractall()
            shutil.move(json_file_name, bin_path)

        with open(info_path, mode="w") as f:
            f.write(json.dumps(info))

    def _get_and_update_dataset_cache(self, **kwargs: Any) -> str:
        # 检查目录，如果不存在目录则创建
        if not os.path.exists(QianfanDatasetLocalCacheDir) or not os.path.isdir(
            QianfanDatasetLocalCacheDir
        ):
            os.makedirs(QianfanDatasetLocalCacheDir)

        cache_dir = os.path.join(
            QianfanDatasetLocalCacheDir,
            str(self.group_id),
            str(self.id),
            str(self.version),
        )
        if not os.path.exists(cache_dir) or not os.path.isdir(cache_dir):
            os.makedirs(cache_dir)

        dataset_info_path = os.path.join(cache_dir, "dataset_info.json")
        dataset_bin_path = os.path.join(cache_dir, "dataset_bin.bin")

        # 如果不存在缓存文件，则创建缓存文件
        if not os.path.exists(dataset_info_path) or not os.path.exists(
            dataset_bin_path
        ):
            print("检查失败，不存在缓存文件，开始下载")
            self._save_remote_into_file(dataset_bin_path, dataset_info_path, **kwargs)

        def _datetime_parse_hook(obj: Any) -> Union[datetime.datetime, str]:
            if isinstance(obj, str):
                try:
                    return dateutil.parser.parser().parse(timestr=obj)
                except Exception:
                    return obj
            return obj

        # 尝试从本地缓存中读取数据
        try:
            with open(dataset_info_path, mode="r") as f:
                dataset_info = json.load(f, object_hook=_datetime_parse_hook)

            qianfan_resp = Data.get_dataset_info(self.id, **kwargs)["result"][
                "versionInfo"
            ]
            parser = dateutil.parser.parser()
            if parser.parse(qianfan_resp["modifyTime"]) > parser.parse(
                dataset_info["finishTime"]
            ):
                # 更新缓存
                print("缓存过期，开始获取数据")
                self._save_remote_into_file(
                    dataset_bin_path, dataset_info_path, **kwargs
                )
        except Exception:
            print("异常，开始获取数据")
            self._save_remote_into_file(dataset_bin_path, dataset_info_path, **kwargs)

        with open(dataset_bin_path, mode="r") as f:
            self.download_when_init = True
            return f.read()

    def _check_is_any_data_existed_in_dataset(self, **kwargs: Any) -> bool:
        qianfan_resp = Data.get_dataset_info(self.id, **kwargs)["result"]["versionInfo"]
        return qianfan_resp["entityCount"] != 0

    def fetch(self, **kwargs: Any) -> str:
        if self.ak and self.sk:
            kwargs["ak"] = self.ak
            kwargs["sk"] = self.sk
        if not self._check_is_any_data_existed_in_dataset(**kwargs):
            raise LookupError("no data exists in dataset")

        return self._get_and_update_dataset_cache(**kwargs)

    async def afetch(self, **kwargs: Any) -> str:
        raise NotImplementedError()

    def format_type(self) -> FormatType:
        assert self.data_format_type
        return self.data_format_type

    def set_format_type(self, format_type: FormatType) -> None:
        # 不支持设置，和数据集类型绑定
        # 文本都是 jsonl
        # 文生图都是 json
        raise NotImplementedError()

    class QianfanRequestError(Exception):
        ...

    @classmethod
    def create_new_bare_datasource_from_local(
        cls,
        name: str,
        template_type: DataTemplateType,
        storage_type: DataStorageType = DataStorageType.PublicBos,
        storage_args: Optional[Dict[str, Any]] = None,
        addition_info: Optional[Dict[str, Any]] = None,
        ak: Optional[str] = None,
        sk: Optional[str] = None,
        **kwargs: Any,
    ) -> "QianfanDataSource":
        project_type, set_type = cls._get_qianfan_dataset_type_tuple(template_type)
        if storage_type == DataStorageType.PrivateBos:
            if not storage_args:
                raise ValueError(
                    "cannot create qianfan dataset with empty storage arguments when"
                    " putting data on private storage"
                )
            if "storage_id" not in storage_args:
                raise ValueError(
                    "storage_id needed when putting data on private storage"
                )
            if "storage_path" not in storage_args:
                raise ValueError(
                    "storage_path needed when putting data on private storage"
                )

        storage_args_pass_through = {} if not storage_args else storage_args
        qianfan_resp = Data.create_bare_dataset(
            name,
            set_type,
            project_type,
            template_type,
            storage_type,
            ak=ak,
            sk=sk,
            **storage_args_pass_through,
            **kwargs,
        )["result"]

        return cls(
            id=qianfan_resp["datasetid"],
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
            storage_region=qianfan_resp["storageInfo"]["region"],
            info=(
                {**qianfan_resp, **addition_info} if addition_info else {**qianfan_resp}
            ),
            data_format_type=_get_data_format_from_template_type(template_type),
            ak=ak,
            sk=sk,
        )

    @classmethod
    def get_existed_datasource_from_qianfan(
        cls,
        dataset_id: int,
        is_download_dataset_to_local: bool = False,
        ak: Optional[str] = None,
        sk: Optional[str] = None,
        **kwargs: Any,
    ) -> "QianfanDataSource":
        qianfan_resp = Data.get_dataset_info(dataset_id, ak=ak, sk=sk, **kwargs)[
            "result"
        ]

        set_type = DataSetType(qianfan_resp["versionInfo"]["dataType"])
        if not set_type:
            raise ValueError(
                f'qianfan set type {qianfan_resp["versionInfo"]["dataType"]} not found'
            )

        project_type = DataProjectType(qianfan_resp["versionInfo"]["projectType"])
        if not project_type:
            raise ValueError(
                f'qianfan project type {qianfan_resp["versionInfo"]["projectType"]} not'
                " found"
            )

        template_type = DataTemplateType(qianfan_resp["versionInfo"]["templateType"])
        if not template_type:
            raise ValueError(
                "qianfan template type"
                f" {qianfan_resp['versionInfo']['templateType']} not found"
            )

        storage_type = DataStorageType(qianfan_resp["versionInfo"]["storageType"])
        if not storage_type:
            raise ValueError(
                f'qianfan storage type {qianfan_resp["versionInfo"]["storageType"]} not'
                " found"
            )

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
            storage_name=qianfan_resp["versionInfo"]["storage"]["storageName"],
            storage_region=qianfan_resp["versionInfo"]["storage"]["region"],
            download_when_init=is_download_dataset_to_local,
            info={**qianfan_resp},
            data_format_type=_get_data_format_from_template_type(template_type),
            ak=ak,
            sk=sk,
        )

        if is_download_dataset_to_local:
            dataset.fetch(**kwargs)

        return dataset
