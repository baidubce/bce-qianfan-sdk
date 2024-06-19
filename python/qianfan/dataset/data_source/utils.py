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
import hashlib
import json
import os
import shutil
import threading
import uuid
import zipfile
from enum import Enum
from pathlib import Path
from time import sleep
from typing import Any, Callable, Dict, Generator, List, Optional, Tuple, Type, Union

import pyarrow
import requests

from qianfan.config import encoding, get_config
from qianfan.dataset.consts import (
    QianfanDatasetCacheFileExtensionName,
    QianfanDatasetLocalCacheDir,
    QianfanDatasetMetaInfoExtensionName,
    QianfanDatasetPackColumnName,
    QianfanDatasetText2ImageUnzipCacheDir,
    QianfanMapperCacheDir,
    Text2ImageAnnotationColumnName,
    Text2ImagePathColumnName,
    _merge_custom_path,
)
from qianfan.dataset.data_source.base import FormatType
from qianfan.dataset.data_source.chunk_reader import (
    BaseReader,
    CsvReader,
    JsonLineReader,
    JsonReader,
    MapperReader,
    TextReader,
)
from qianfan.dataset.table_utils import _construct_packed_table_from_nest_sequence
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
from qianfan.utils.bos_uploader import BosHelper, generate_bos_file_path
from qianfan.utils.pydantic import BaseModel

try:
    import dateutil.parser
except ImportError:
    log_warn("python-dateutil not installed, only online function can be used")


class ImageExtensionName(Enum):
    """Enum for image extension name"""

    Jpg = "jpg"
    Jpeg = "jpeg"
    Png = "png"
    Bmp = "bmp"


class TaskDispatcher:
    def __init__(self, batch_size: int, task_number: int):
        self.task_queue: List[Tuple[int, int]] = []
        for batch_index in range(0, task_number, batch_size):
            current_batch_size = min(task_number - batch_index, batch_size)
            self.task_queue.append((batch_index, current_batch_size))

        self.lock = threading.Lock()
        self.current_task_queue_index = 0

    def get_task(self) -> Optional[Tuple[int, int]]:
        with self.lock:
            if self.current_task_queue_index >= len(self.task_queue):
                return None

            task = self.task_queue[self.current_task_queue_index]
            self.current_task_queue_index += 1
            return task

    def mapper_closure(
        self, func: Callable[[int, int], Generator[Any, None, None]]
    ) -> Callable[[], Generator[Tuple[int, Any], None, None]]:
        def new_func() -> Generator[Tuple[int, Any], None, None]:
            task_slice = self.get_task()
            while task_slice:
                batch_index, batch_size = task_slice[0], task_slice[1]
                returned_data_list: List[Any] = []

                for returned_data in func(batch_index, batch_size):
                    returned_data_list.append(returned_data)

                yield batch_index, returned_data_list
                task_slice = self.get_task()

        return new_func


def _get_annotation_file_name(file_name: str) -> str:
    return file_name[: file_name.rfind(".")] + ".json"


def _get_all_image_files_and_annotations_from_root(
    root: str, files: List[str]
) -> Tuple[List[str], List[Optional[Dict]]]:
    image_extension_name_tuple = tuple([name.value for name in ImageExtensionName])

    result_image_path_list: List[str] = []
    result_annotation_path_list: List[Optional[Dict]] = []

    for file_name in files:
        if not file_name.endswith(image_extension_name_tuple):
            continue

        file_path = os.path.abspath(os.path.join(root, file_name))
        result_image_path_list.append(file_path)

        annotation_file_path = _get_annotation_file_name(file_path)
        if os.path.exists(annotation_file_path):
            with open(annotation_file_path, encoding=encoding()) as f:
                result_annotation_path_list.append(json.load(f))
        else:
            result_annotation_path_list.append(None)

    return result_image_path_list, result_annotation_path_list


def _read_all_image_in_an_folder(path: str, **kwargs: Any) -> pyarrow.Table:
    table_list: List[pyarrow.Table] = []

    for root, dirs, files in os.walk(path):
        result = _get_all_image_files_and_annotations_from_root(root, files)
        table_list.append(
            pyarrow.Table.from_pydict(
                {
                    Text2ImagePathColumnName: result[0],
                    Text2ImageAnnotationColumnName: result[1],
                }
            )
        )

    return pyarrow.concat_tables(table_list)


def _read_all_image_from_zip(path: str, **kwargs: Any) -> pyarrow.Table:
    """从压缩包中读取所有的文件"""
    tmp_folder_path = os.path.join(
        _merge_custom_path(QianfanDatasetText2ImageUnzipCacheDir),
        f"image_dataset_folder_{uuid.uuid4()}",
    )
    with zipfile.ZipFile(path) as zip_file:
        zip_file.extractall(tmp_folder_path)
    return _read_all_image_in_an_folder(tmp_folder_path, **kwargs)


def _collect_all_images_and_annotations_in_one_folder(
    table: pyarrow.Table, target_folder_path: str
) -> None:
    os.makedirs(target_folder_path, exist_ok=True)
    for entry in table.to_pylist():
        file_path = entry[Text2ImagePathColumnName]
        annotation_info = entry[Text2ImageAnnotationColumnName]

        # 构建目标文件路径
        target_file_path = os.path.join(target_folder_path, os.path.split(file_path)[1])

        # 拷贝文件
        shutil.copy(file_path, target_file_path)

        # 如果附带标注信息，则创建标注信息
        if annotation_info:
            with open(
                _get_annotation_file_name(target_file_path),
                mode="w",
                encoding=encoding(),
            ) as f:
                json.dump(annotation_info, f)


class _DatasetCacheMetaInfo(BaseModel):
    """存储数据集缓存中的，单个文件的元信息"""

    # 源文件的路径
    source_file_path: str

    # 源文件的哈希值
    source_file_hash: str

    # 缓存文件的路径: str
    cache_file_path: str


def _read_all_file_content_in_an_folder(
    path: str, format_type: FormatType, **kwargs: Any
) -> pyarrow.Table:
    """从文件夹里读取所有指定类型的的文件"""
    og_table_list: List[pyarrow.Table] = []

    # 如果是文件夹，则遍历读取
    for root, dirs, files in os.walk(path):
        for file_name in files:
            if not file_name.endswith(format_type.value):
                continue
            file_path = os.path.join(root, file_name)

            table = _get_a_pyarrow_table(file_path, format_type, **kwargs)
            og_table_list.append(table)

    og_table = pyarrow.concat_tables(og_table_list)
    assert isinstance(og_table, pyarrow.Table)
    og_table.combine_chunks()
    return og_table


def _read_all_file_from_zip(
    path: str, format_type: FormatType, **kwargs: Any
) -> pyarrow.Table:
    """从压缩包中读取所有的文件"""
    tmp_folder_path = "tmp_folder_path"
    try:
        with zipfile.ZipFile(path) as zip_file:
            zip_file.extractall(tmp_folder_path)
        return _read_all_file_content_in_an_folder(
            tmp_folder_path, format_type, **kwargs
        )
    finally:
        shutil.rmtree(tmp_folder_path, ignore_errors=True)


def _get_reader_class(format_type: FormatType) -> Type[BaseReader]:
    if format_type == FormatType.Jsonl:
        return JsonLineReader
    elif format_type == FormatType.Csv:
        return CsvReader
    elif format_type == FormatType.Json:
        return JsonReader
    elif format_type == FormatType.Text:
        return TextReader
    else:
        err_msg = f"unsupported file reader type: {format_type.value}"
        log_error(err_msg)
        raise ValueError(err_msg)


def _has_cache_been_disabled(**kwargs: Any) -> bool:
    return kwargs.get("disable_cache", False) or get_config().DISABLE_CACHE


def _get_a_pyarrow_table(
    path: str, format_type: FormatType, **kwargs: Any
) -> pyarrow.Table:
    reader = _get_reader_class(format_type)(file_path=path, **kwargs)

    if _has_cache_been_disabled(**kwargs):
        log_info("has got a non-memory-mapped table")
        return _read_table_and_concat(reader)

    cache_file_path = _get_cache_file_path_and_check_cache_validity(path, reader)
    table = _read_mmap_table_from_arrow_file(cache_file_path)
    log_info("has got a memory-mapped table")
    return table


def _create_mapped_arrow_table(
    path: str,
    mapper_closure: Callable,
    batch_size: int,
    task_number: int,
    **kwargs: Any,
) -> pyarrow.Table:
    task_dispatcher = TaskDispatcher(batch_size, task_number)

    reader = MapperReader(
        mapper_closure=task_dispatcher.mapper_closure(mapper_closure), **kwargs
    )

    if _has_cache_been_disabled(**kwargs):
        return _read_table_and_concat(reader)

    tmp_folder_path, file_name = _construct_buffer_folder_path_and_file_name(
        _merge_custom_path(QianfanMapperCacheDir), path
    )
    tmp_arrow_file_path = os.path.join(
        tmp_folder_path,
        f"{file_name}_{uuid.uuid4()}{QianfanDatasetCacheFileExtensionName}",
    )

    _write_table_to_arrow_file(tmp_arrow_file_path, reader)
    _remove_previous_folder_file(tmp_arrow_file_path)
    return _read_mmap_table_from_arrow_file(tmp_arrow_file_path)


def _iterate_to_conduct_result(
    mapper_closure: Callable,
    batch_size: int,
    task_number: int,
    **kwargs: Any,
) -> List[Any]:
    task_dispatcher = TaskDispatcher(batch_size, task_number)

    reader = MapperReader(
        mapper_closure=task_dispatcher.mapper_closure(mapper_closure), **kwargs
    )
    result_list: List[Any] = []
    for elem in reader:
        for e in elem:
            if e is None:
                raise ValueError("cant return None")
            if not isinstance(e, bool):
                raise ValueError("returned value isn't bool")
        result_list.extend(elem)

    return result_list


def _pure_iterate(
    mapper_closure: Callable,
    batch_size: int,
    task_number: int,
    **kwargs: Any,
) -> None:
    task_dispatcher = TaskDispatcher(batch_size, task_number)

    reader = MapperReader(
        mapper_closure=task_dispatcher.mapper_closure(mapper_closure), **kwargs
    )

    for _ in reader:
        continue

    return


def _read_mmap_table_from_arrow_file(arrow_file_path: str) -> pyarrow.Table:
    log_info(f"start to get memory_map from {arrow_file_path}")
    with pyarrow.memory_map(arrow_file_path) as mmap_stream:
        return pyarrow.ipc.open_stream(mmap_stream).read_all()


def _remove_previous_folder_file(path: str) -> None:
    dir_path, og_file_name = os.path.split(path)
    for root, dirs, files in os.walk(dir_path):
        for file_name in files:
            if not file_name.endswith(QianfanDatasetCacheFileExtensionName):
                continue
            file_path = os.path.join(root, file_name)
            if file_name != og_file_name:
                try:
                    os.remove(file_path)
                except Exception:
                    continue


def _construct_buffer_folder_path_and_file_name(
    base_path: Union[str, Path], file_path: str
) -> Tuple[str, str]:
    # 获取源文件的绝对路径
    abs_file_path: str = os.path.abspath(file_path)

    # 获取绝对路径中的文件夹路径和文件名
    dir_path, file_name = os.path.split(abs_file_path)
    assert isinstance(dir_path, str) and isinstance(file_name, str)

    file_name_without_extension_name: str = file_name.split(".")[0]

    # 根据绝对路径来创建缓存文件夹
    cache_path_dir: str = os.path.join(
        base_path, dir_path[dir_path.find(os.path.sep) + 1 :]
    )
    os.makedirs(cache_path_dir, exist_ok=True)

    return cache_path_dir, file_name_without_extension_name


def _get_cache_file_path_and_check_cache_validity(
    file_path: str, reader: BaseReader
) -> str:
    cache_path_dir, file_name_without_extension_name = (
        _construct_buffer_folder_path_and_file_name(
            _merge_custom_path(QianfanDatasetLocalCacheDir), file_path
        )
    )
    abs_file_path: str = os.path.abspath(file_path)

    # 计算源文件的哈希值，默认使用 md5 算法
    hash_value: str = _calculate_file_hash(file_path)

    # 构造元信息文件路径
    meta_info_path = os.path.join(
        cache_path_dir,
        file_name_without_extension_name + QianfanDatasetMetaInfoExtensionName,
    )

    # 如果缓存的元信息文件存在，则读取
    if os.path.exists(meta_info_path):
        with open(meta_info_path, mode="r", encoding=encoding()) as f:
            cache_meta = _DatasetCacheMetaInfo(**json.load(f))

        # 如果文件哈希值与记录得到的哈希值一致，则直接返回缓存的 arrow 文件
        if cache_meta.source_file_hash == hash_value:
            return cache_meta.cache_file_path

    # 如果不一致，则需要重新更新缓存
    log_info(f"need create cached arrow file for {abs_file_path}")

    cache_file_path = os.path.join(
        cache_path_dir,
        file_name_without_extension_name + QianfanDatasetCacheFileExtensionName,
    )

    cache_meta = _DatasetCacheMetaInfo(
        source_file_path=abs_file_path,
        source_file_hash=hash_value,
        cache_file_path=cache_file_path,
    )
    cache_meta.source_file_path = abs_file_path
    cache_meta.source_file_hash = hash_value
    cache_meta.cache_file_path = cache_file_path

    # 创建缓存文件
    _write_table_to_arrow_file(cache_file_path, reader)

    # 更新缓存元信息
    with open(meta_info_path, "w", encoding=encoding()) as meta:
        meta.write(cache_meta.json())

    return cache_file_path


def _calculate_file_hash(file_path: str, hash_algorithm: str = "md5") -> str:
    # 创建哈希对象
    hasher = hashlib.new(hash_algorithm)

    # 以二进制模式打开文件
    with open(file_path, "rb") as file:
        # 逐块读取文件内容并更新哈希对象
        for chunk in iter(lambda: file.read(4096), b""):
            result = hasher.digest() + chunk
            hasher = hashlib.new(hash_algorithm)
            hasher.update(result)

    # 返回计算得到的哈希值
    return hasher.hexdigest()


def _read_table_and_concat(reader: BaseReader) -> pyarrow.Table:
    returned_table_list: List[pyarrow.Table] = []

    for table in _build_table_from_reader(reader):
        returned_table_list.append(table)

    return pyarrow.concat_tables(returned_table_list)


def _write_table_to_arrow_file(cache_file_path: str, reader: BaseReader) -> None:
    import filelock

    stream_writer: Optional[pyarrow.ipc.RecordBatchStreamWriter] = None

    log_info(f"start to write arrow table to {cache_file_path}")

    file_lock = filelock.FileLock(cache_file_path + ".lock")

    file_lock.acquire()
    for table in _build_table_from_reader(reader):
        assert isinstance(table, pyarrow.Table)
        if stream_writer is None:
            stream_writer = pyarrow.ipc.new_stream(cache_file_path, table.schema)

        stream_writer.write_table(table)

    assert stream_writer
    stream_writer.close()
    file_lock.release()

    log_info("writing succeeded")
    return


def _build_table_from_reader(reader: BaseReader) -> pyarrow.Table:
    reader_type = type(reader)
    for elem_list in reader:
        if (
            reader_type == CsvReader
            or reader_type == TextReader
            or (reader_type == JsonReader and isinstance(elem_list[0], dict))
            or (reader_type == JsonLineReader and isinstance(elem_list[0], dict))
        ):
            table = pyarrow.Table.from_pylist(elem_list)
        elif (
            reader_type == JsonLineReader or reader_type == JsonReader
        ) and isinstance(elem_list[0], list):
            table = _construct_packed_table_from_nest_sequence(elem_list)
        elif reader_type == MapperReader:
            if isinstance(elem_list[0], (list, str)):
                table = pyarrow.Table.from_pydict(
                    {QianfanDatasetPackColumnName: elem_list}
                )
            elif isinstance(elem_list[0], dict):
                table = pyarrow.Table.from_pylist(elem_list)
            else:
                err_msg = (
                    "get unsupported element type from the return value of map"
                    f" function: {type(elem_list[0])} with value: {elem_list[0]}"
                )
                log_error(err_msg)
                raise ValueError(err_msg)
        else:
            err_msg = "unsupported format when reading file as dataset"
            log_error(err_msg)
            raise ValueError(err_msg)

        table.combine_chunks()
        yield table


# 创建压缩包
def zip_file_or_folder(path: str) -> str:
    folder_name: str = os.path.split(os.path.abspath(path))[1]

    if folder_name.rfind(".") != 0:
        # 去除文件内的后缀名
        folder_name = folder_name[0 : folder_name.rfind(".")]
        # 去除文件前的英文句号
        folder_name = folder_name.strip(".")

    # 如果是文件夹，则直接调用对应的函数处理
    if os.path.isdir(path):
        return shutil.make_archive(folder_name, "zip", root_dir=path)

    # 不然得要手动处理文件
    zip_file_name = f"{folder_name}.zip"
    with zipfile.ZipFile(zip_file_name, mode="w") as zip_file:
        zip_file.write(path)

    # 取绝对路径的前缀文件夹并拼接压缩文件名组成路径
    return os.path.join(os.path.split(os.path.abspath(path))[0], zip_file_name)


# 使用 DataTemplateType 来推断配对的 FormatType
def _get_data_format_from_template_type(template_type: DataTemplateType) -> FormatType:
    """从千帆的 DataTemplateType 来推断 FormatType"""
    if template_type in [
        DataTemplateType.NonSortedConversation,
        DataTemplateType.SortedConversation,
        DataTemplateType.QuerySet,
        DataTemplateType.PromptChosenRejected,
    ]:
        return FormatType.Jsonl
    elif template_type == DataTemplateType.GenericText:
        return FormatType.Text
    elif template_type == DataTemplateType.Text2Image:
        return FormatType.Text2Image
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


def upload_data_from_bos_to_qianfan(
    bos_helper: BosHelper,
    is_zip_file: bool,
    qianfan_dataset_id: str,
    storage_id: str,
    remote_file_path: str,
    is_annotated: bool = False,
) -> None:
    # 如果不是压缩包，则直接导入
    if not is_zip_file:
        complete_file_path = generate_bos_file_path(storage_id, remote_file_path)
        if not _create_import_data_task_and_wait_for_success(
            qianfan_dataset_id, is_annotated, complete_file_path
        ):
            err_msg = "import data from bos file failed"
            log_error(err_msg)
            raise ValueError(err_msg)

    # 不然需要创建分享链接导入
    else:
        shared_str = bos_helper.get_bos_file_shared_url(remote_file_path, storage_id)
        log_info(f"get shared file url: {shared_str}")
        if not _create_import_data_task_and_wait_for_success(
            qianfan_dataset_id, is_annotated, shared_str, DataSourceType.SharedZipUrl
        ):
            err_msg = "import data from shared zip url failed"
            log_error(err_msg)
            raise ValueError(err_msg)


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
