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
utilities for data source
"""
import datetime
import os
import shutil
import zipfile
from time import sleep
from typing import Any, Dict, List, Optional, Tuple, Union

import dateutil.parser
import requests

from qianfan.config import encoding, get_config
from qianfan.dataset.data_source.base import FormatType
from qianfan.errors import QianfanRequestError
from qianfan.resources import Data
from qianfan.resources.console.consts import (
    DataExportDestinationType,
    DataExportStatus,
    DataImportStatus,
    DataProjectType,
    DataReleaseStatus,
    DataSetType,
    DataSourceType,
    DataTemplateType,
)
from qianfan.utils import log_debug, log_error, log_info, log_warn


def _read_all_file_content_in_an_folder(
    path: str, format_type: FormatType
) -> List[str]:
    """从文件夹里读取所有指定类型的的文件"""
    ret_list: List[str] = []

    # 不保证文件读取的顺序性
    for root, dirs, files in os.walk(path):
        for file_name in files:
            if not file_name.endswith(format_type.value):
                continue

            file_path = os.path.join(root, file_name)
            with open(file_path, mode="r", encoding=encoding()) as f:
                ret_list.append(f.read())

    return ret_list


def _read_all_file_from_zip(path: str, format_type: FormatType) -> List[str]:
    """从压缩包中读取所有的文件"""
    tmp_folder_path = "tmp_folder_path"
    try:
        with zipfile.ZipFile(path) as zip_file:
            zip_file.extractall(tmp_folder_path)
        return _read_all_file_content_in_an_folder(tmp_folder_path, format_type)
    finally:
        shutil.rmtree(tmp_folder_path, ignore_errors=True)


# 使用 DataTemplateType 来推断配对的 FormatType
def _get_data_format_from_template_type(template_type: DataTemplateType) -> FormatType:
    """从千帆的 DataTemplateType 来推断 FormatType"""
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
    dataset_id: str,
    is_annotated: bool,
    file_path: str,
    source_type: DataSourceType = DataSourceType.PrivateBos,
) -> bool:
    """创建并且监听导出任务直到完成"""

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


def _get_qianfan_dataset_type_tuple(
    template_type: DataTemplateType,
) -> Tuple[DataProjectType, DataSetType]:
    for t in DataProjectType:
        # DataProjectType 是匹配的 DataTemplateType 的前缀
        # 具体来说，DataTemplateType 在整除 100 后得到的整数
        # 即是 DataProjectType
        # 此处通过整数除法计算前缀
        if template_type.value // t.value == 100:
            if template_type == DataTemplateType.Text2Image:
                log_debug(
                    f"inferred project type: {t}, set type: {DataSetType.MultiModel}"
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


def _get_latest_export_record(
    dataset_id: str, **kwargs: Any
) -> Tuple[Dict, datetime.datetime]:
    """从平台获取最新的数据集导出记录信息，以及它的导出时间"""
    parser = dateutil.parser.parser()
    export_records = Data.get_dataset_export_records(dataset_id, **kwargs)["result"]
    log_info(f"get export records succeeded for dataset id {dataset_id}")
    newest_record_index, latest_record_time = 0, datetime.datetime(1970, 1, 1)

    for index in range(len(export_records)):
        record = export_records[index]
        try:
            date = parser.parse(record["finishTime"])
            if date > latest_record_time:
                newest_record_index = index
                latest_record_time = date
        except Exception as e:
            log_warn(f"an exception occurred when fetch export records info: {str(e)}")
            continue

    log_info(f"latest dataset with time{latest_record_time} for dataset {dataset_id}")
    return export_records[newest_record_index], latest_record_time


# json 解析钩子，将值中的时间戳字符串解析为 datetime 对象
def _datetime_parse_hook(obj: Any) -> Union[datetime.datetime, str]:
    if isinstance(obj, str):
        try:
            return dateutil.parser.parser().parse(timestr=obj)
        except Exception:
            return obj
    return obj


def _check_is_any_data_existed_in_dataset(dataset_id: str, **kwargs: Any) -> bool:
    """检查远端数据集是否为空"""

    qianfan_resp = Data.get_dataset_info(dataset_id, **kwargs)["result"]["versionInfo"]
    return qianfan_resp["entityCount"] != 0


def _check_data_and_zip_file_valid(
    data: Optional[str], zip_file_path: Optional[str]
) -> None:
    if data and zip_file_path:
        err_msg = "can't set 'data' and 'zip_file_path' simultaneously"
        log_error(err_msg)
        raise ValueError(err_msg)

    if not data and not zip_file_path:
        err_msg = "must set either 'data' or 'zip_file_path'"
        log_error(err_msg)
        raise ValueError(err_msg)


def _create_export_data_task_and_wait_for_success(
    dataset_id: str, **kwargs: Any
) -> None:
    log_info("start to export dataset")
    Data.create_dataset_export_task(
        dataset_id, DataExportDestinationType.PlatformBos, **kwargs
    )
    log_info("create dataset export task successfully")

    # 轮巡导出状态
    while True:
        sleep(get_config().EXPORT_STATUS_POLLING_INTERVAL)
        log_info("polling export task status")
        info = Data.get_dataset_info(dataset_id, **kwargs)["result"]["versionInfo"]
        status = info["exportStatus"]

        if status == DataExportStatus.Finished.value:
            log_info("export succeed")
            break
        elif status == DataExportStatus.Running.value:
            log_info(f"export status: {status}, keep polling")
            continue
        elif status == DataExportStatus.Failed.value:
            error = QianfanRequestError(f"export dataset failed with status {status}")
            log_error(str(error))
            raise error


def _download_file_from_url_streamly(
    download_url: str, destination_file_path: str
) -> None:
    log_info(f"start to download file from url {download_url}")
    try:
        resp = requests.get(download_url, stream=True)
        with open(destination_file_path, "wb") as f:
            for chuck in resp.iter_content(10240):
                f.write(chuck)
        resp.close()
    except Exception as e:
        log_error(f"exception occurred during download {str(e)}")
        raise e

    if resp.status_code != 200:
        http_error = Exception(
            f"download file from url {download_url} failed with http status code"
            f" {resp.status_code}"
        )
        log_error(str(http_error))
        raise http_error


def _create_release_data_task_and_wait_for_success(
    dataset_id: str, **kwargs: Any
) -> bool:
    info = Data.get_dataset_info(dataset_id, **kwargs)["result"]["versionInfo"]

    status = info["releaseStatus"]
    if status == DataReleaseStatus.Finished:
        return True

    Data.release_dataset(dataset_id, **kwargs)
    while True:
        sleep(get_config().RELEASE_STATUS_POLLING_INTERVAL)

        info = Data.get_dataset_info(dataset_id)["result"]["versionInfo"]
        status = info["releaseStatus"]

        if status == DataReleaseStatus.Running:
            log_info("data releasing, keep polling")
            continue
        elif status == DataReleaseStatus.Failed:
            message = f"data releasing failed with error code {info['releaseErrCode']}"
            log_error(message)
            return False
        else:
            log_info("data releasing succeeded")
            return True
