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
dataset core concept, a wrap of data processing, data transmission and data validation
"""

import csv
import functools
import io
import json
import uuid
from time import sleep
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple, Union

import pyarrow.json
import requests
from typing_extensions import Self

from qianfan import get_config
from qianfan.dataset.consts import (
    QianfanDataGroupColumnName,
)
from qianfan.dataset.data_operator import QianfanOperator
from qianfan.dataset.data_source import (
    DataSource,
    FileDataSource,
    FormatType,
    QianfanDataSource,
)
from qianfan.dataset.schema import (
    QianfanGenericText,
    QianfanQuerySet,
    QianfanSchema,
    QianfanSortedConversation,
    QianfanText2Image,
    Schema,
)
from qianfan.dataset.table import Table
from qianfan.errors import RequestError, ValidationError
from qianfan.resources import Data
from qianfan.resources.console.consts import DataTemplateType, ETLTaskStatus
from qianfan.utils import log_debug, log_error, log_info, log_warn


# 装饰器，用来阻塞部分对云上数据集（非本地）的操作请求
def _online_except_decorator(func: Callable) -> Callable:
    @functools.wraps(func)
    def inner(dataset: Any, *args: Any, **kwargs: Any) -> Any:
        if dataset._is_dataset_located_in_qianfan():  # noqa
            raise Exception()
        return func(dataset, *args, **kwargs)

    return inner


class Dataset(Table):
    """Dataset"""

    # 内部的数据源对象，在 load 时被指定
    inner_data_source_cache: Optional[DataSource] = None

    # schema 对象的缓存，在 load 时被指定
    inner_schema_cache: Optional[Schema] = None

    @classmethod
    def _from_source(
        cls, source: DataSource, schema: Optional[Schema], **kwargs: Any
    ) -> "Dataset":
        """内部封装的从数据源导出字节流并构建数据集的方法"""
        if isinstance(source, QianfanDataSource) and not source.download_when_init:
            # 如果是云上的数据集，则直接创建空表。
            # 云上数据集的相关处理能力暂不可用
            log_info("a cloud dataset has been created")
            return cls(
                inner_table=pyarrow.Table.from_pylist([{"place_holder": 1}]),
                inner_data_source_cache=source,
                inner_schema_cache=schema,
            )

        # 从数据源获取字符串格式的数据集。以及数据集的解析格式
        str_content = source.fetch(**kwargs)
        format_type = source.format_type()

        log_debug(
            f"content (type: {format_type}) fetched from data source: \n{str_content}"
        )

        if format_type == FormatType.Json:
            data_py_rep = json.loads(str_content)
            # 如果导入的是一个字典，则需要转换成列表才能被读取
            if not isinstance(data_py_rep, list):
                data_py_rep = [data_py_rep]
            pyarrow_table = pyarrow.Table.from_pylist(data_py_rep)
        elif format_type == FormatType.Jsonl:
            json_data_list = [
                json.loads(line) for line in str_content.split("\n") if line
            ]
            if not json_data_list:
                raise ValueError("no data in jsonline file")
            if isinstance(json_data_list[0], list):
                inner_list: List[Dict[str, Any]] = []
                for i in range(len(json_data_list)):
                    for pair in json_data_list[i]:
                        inner_list.append({**pair, QianfanDataGroupColumnName: i})
                pyarrow_table = pyarrow.Table.from_pylist(inner_list)
            elif isinstance(json_data_list[0], dict):
                # 如果读取的是一个 Json 字典的列表，则正常存储，此时行列的处理能力可用
                pyarrow_table = pyarrow.Table.from_pylist(json_data_list)
            else:
                error = TypeError(
                    f"unknown table element type: {type(json_data_list[0])}"
                )
                log_error(str(error))
                raise error
        elif format_type == FormatType.Csv:
            # csv 不支持嵌套格式
            csv_data = [row for row in csv.DictReader(str_content)]
            pyarrow_table = pyarrow.Table.from_pylist(csv_data)
        elif format_type == FormatType.Text:
            # 如果是纯文本，则放置在 prompt 一列下
            line_data = [{"prompt": line} for line in str_content.split("\n")]
            pyarrow_table = pyarrow.Table.from_pylist(line_data)
        else:
            error = ValueError(f"unknown format type: {format_type}")
            log_error(str(error))
            raise error

        return cls(
            inner_table=pyarrow_table,
            inner_data_source_cache=source,
            inner_schema_cache=schema,
        )

    def _to_source(self, source: DataSource, **kwargs: Any) -> bool:
        """内部封装的，将数据集序列化并导出字节流到数据源的方法"""
        format_type = source.format_type()

        log_info(f"export as format: {format_type}")

        if format_type == FormatType.Json:
            # 如果是 json，则直接导出，此时不关注内部是否嵌套。
            dict_list = self.inner_table.to_pylist()
            return source.save(json.dumps(dict_list, ensure_ascii=False), **kwargs)

        elif format_type == FormatType.Jsonl:
            list_of_json: List[str] = []

            # 如果是 Jsonl，则需要处理可能的分组情况
            column_names = self.inner_table.column_names
            if QianfanDataGroupColumnName in column_names:
                compo_list: List[List[Dict[str, Any]]] = []
                for row in self.inner_table.to_pylist():
                    group_index = row[QianfanDataGroupColumnName]
                    while group_index >= len(compo_list):
                        compo_list.append([])
                    row.pop(QianfanDataGroupColumnName)
                    compo_list[group_index].append(row)

                for elem in compo_list:
                    list_of_json.append(json.dumps(elem, ensure_ascii=False))
            elif isinstance(source, QianfanDataSource):
                # 导出到千帆且非嵌套时需要使用特殊格式，只支持文本类数据
                dict_list = self.inner_table.to_pylist()
                for elem in dict_list:
                    list_of_json.append(f"[{json.dumps(elem, ensure_ascii=False)}]")
            else:
                dict_list = self.inner_table.to_pylist()
                for elem in dict_list:
                    list_of_json.append(json.dumps(elem, ensure_ascii=False))
            return source.save("\n".join(list_of_json), **kwargs)

        elif format_type == FormatType.Csv:
            string_stream_buffer = io.StringIO()
            pyarrow.csv.write_csv(self.inner_table, string_stream_buffer)
            return source.save(string_stream_buffer.getvalue(), **kwargs)

        elif format_type == FormatType.Text:
            # 导出为纯文本时，列的数量不可大于 1
            if self.get_column_count() > 1:
                error = ValueError(
                    "cannot export dataset to pure text if the number of column is"
                    " greater than 1"
                )
                log_error(str(error))
                raise error
            result_list = list(self.inner_table.to_pydict().values())[0]
            return source.save("\n".join(result_list), **kwargs)

        else:
            error = ValueError(f"unknown format type: {format_type}")
            log_error(str(error))
            raise error

    @classmethod
    def _from_args_to_source(
        cls,
        data_file: Optional[str] = None,
        qianfan_dataset_id: Optional[int] = None,
        qianfan_dataset_create_args: Optional[Dict[str, Any]] = None,
        huggingface_name: Optional[str] = None,
        **kwargs: Any,
    ) -> Optional[DataSource]:
        """从参数来构建数据源"""
        if data_file:
            log_info(
                f"construct a file data source from path: {data_file}, with args:"
                f" {kwargs}"
            )
            return FileDataSource(path=data_file, **kwargs)
        if qianfan_dataset_id:
            log_info(
                "construct a qianfan data source from existed id:"
                f" {qianfan_dataset_id}, with args: {kwargs}"
            )
            return QianfanDataSource.get_existed_dataset(
                dataset_id=qianfan_dataset_id, **kwargs
            )
        if qianfan_dataset_create_args:
            log_info(
                "construct a new qianfan data source from args:"
                f" {qianfan_dataset_create_args}, with args: {kwargs}"
            )
            return QianfanDataSource.create_bare_dataset(**qianfan_dataset_create_args)
        if huggingface_name:
            error = ValueError("huggingface not supported yet")
            log_error(str(error))
            raise error

        log_info("no datasource was constructed")
        return None

    @classmethod
    def _get_qianfan_schema(cls, source: QianfanDataSource) -> Schema:
        """推断获取 Schema"""
        template_type = source.template_type
        if template_type == DataTemplateType.SortedConversation:
            return QianfanSortedConversation()
        if template_type == DataTemplateType.NonSortedConversation:
            return QianfanSortedConversation()
        if template_type == DataTemplateType.GenericText:
            return QianfanGenericText()
        if template_type == DataTemplateType.QuerySet:
            return QianfanQuerySet()
        if template_type == DataTemplateType.Text2Image:
            return QianfanText2Image()

        error = ValueError(f"schema didn't find for template type {template_type}")
        log_error(str(error))
        raise error

    @classmethod
    def load(
        cls,
        source: Optional[DataSource] = None,
        data_file: Optional[str] = None,
        qianfan_dataset_id: Optional[int] = None,
        huggingface_name: Optional[str] = None,
        schema: Optional[Schema] = None,
        **kwargs: Any,
    ) -> "Dataset":
        """
        Read data from the source or create a source from the parameters
        and create a Table instance.
        If a schema is specified, perform validation after importing.

        Args:
            source (Optional[DataSource]): where dataset load from,
                default to None，in which case,
                a datasource will be created inside dataset
                using parameters below
            data_file (Optional[str]):
                dataset local file path, default to None
            qianfan_dataset_id (Optional[int]):
                qianfan dataset ID, default to None
            huggingface_name (Optional[str]):
                Hugging Face dataset name, not available now
            schema: (Optional[Schema]):
                schema used to validate loaded data, default to None
            kwargs (Any): optional arguments

        Returns:
            Dataset: a dataset instance
        """

        if not source:
            log_info("no data source was provided, construct")
            source = cls._from_args_to_source(
                data_file=data_file,
                qianfan_dataset_id=qianfan_dataset_id,
                huggingface_name=huggingface_name,
                **kwargs,
            )

        # 从数据源开始构建对象
        assert source
        table = cls._from_source(source, schema, **kwargs)

        # 校验
        if schema and not schema.validate(table):
            error = ValidationError("validate failed when initialize dataset")
            log_error(str(error))
            raise error

        return table

    def save(
        self,
        destination: Optional[DataSource] = None,
        data_file: Optional[str] = None,
        qianfan_dataset_id: Optional[int] = None,
        qianfan_dataset_create_args: Optional[Dict[str, Any]] = None,
        huggingface_name: Optional[str] = None,
        schema: Optional[Schema] = None,
        **kwargs: Any,
    ) -> bool:
        """
        Write data to source
        if a schema has been passed,
        validate data before exporting

        Args:
            destination (Optional[DataSource]):
                data source where dataset exports，default to None.
                in which case, a datasource will be created inside dataset
                using parameters below
            data_file (Optional[str]):
                dataset local file path, default to None
            qianfan_dataset_id (Optional[int]):
                qianfan dataset ID, default to None
            qianfan_dataset_create_args: (Optional[Dict[str: Any]]):
                create arguments for creating a bare dataset on qianfan,
                default to None
            huggingface_name (Optional[str]):
                Hugging Face dataset name, not available now
            schema: (Optional[Schema]):
                schema used to validate before exporting data, default to None
            kwargs (Any): optional arguments

        Returns:
            bool: is saving succeeded
        """
        if not destination:
            log_info("no destination data source was provided, construct")
            destination = self._from_args_to_source(
                data_file,
                qianfan_dataset_id,
                qianfan_dataset_create_args,
                huggingface_name,
                **kwargs,
            )

        # 获取数据源参数
        source = destination if destination else self.inner_data_source_cache
        assert source

        # 首先检查是否有传入 schema 或者已经默认有了 schema
        schema = schema if schema else self.inner_schema_cache
        # 如果导出的数据源是千帆，则强制构造 schema 进行检查，优先级最高
        if isinstance(source, QianfanDataSource):
            # 一个方法从 source 中抽取 schema 信息
            schema = self._get_qianfan_schema(source)

        # 校验
        if schema and not schema.validate(self):
            error = ValidationError("validate failed when initialize dataset")
            log_error(str(error))
            raise error

        if isinstance(source, QianfanDataSource):
            assert isinstance(schema, QianfanSchema)
            kwargs["is_annotated"] = schema.is_annotated

        # 开始写入数据
        return self._to_source(source, **kwargs)  # noqa

    @classmethod
    def create_from_pyobj(
        cls,
        data: Union[List[Dict[str, Any]], Dict[str, List]],
        schema: Optional[Schema] = None,
    ) -> "Dataset":
        """
        create a dataset from python dict or list

        Args:
            data (Union[List[Dict[str, Any]], Dict[str, List]]):
                python object used to create dataset。
            schema (Optional[Schema]):
                schema used to validate before exporting data, default to None

        Returns:
            Dataset: a dataset instance
        """
        if isinstance(data, list):
            return cls(
                inner_table=pyarrow.Table.from_pylist(data),
                inner_schema_cache=schema,
            )
        else:
            return cls(
                inner_table=pyarrow.Table.from_pydict(data),
                inner_schema_cache=schema,
            )

    @classmethod
    def create_from_pyarrow_table(
        cls, table: pyarrow.Table, schema: Optional[Schema] = None
    ) -> "Dataset":
        """
        create a dataset from pyarrow table

        Args:
            table (pyarrow): pyarrow table object used to create dataset。
            schema (Optional[Schema]):
                schema used to validate before exporting data, default to None

        Returns:
            Dataset: a dataset instance
        """
        return cls(inner_table=table, inner_schema_cache=schema)

    def _is_dataset_located_in_qianfan(self) -> bool:
        if not isinstance(self.inner_data_source_cache, QianfanDataSource):
            return False
        return not self.inner_data_source_cache.download_when_init

    def _is_dataset_generic_text(self) -> bool:
        if not isinstance(self.inner_data_source_cache, QianfanDataSource):
            return False
        return (
            self.inner_data_source_cache.template_type == DataTemplateType.GenericText
        )

    def _create_a_dataset_etl_task(
        self, operator_dict: Dict[str, List[Dict[str, Any]]]
    ) -> Tuple[int, int]:
        origin_data_source = self.inner_data_source_cache
        assert isinstance(origin_data_source, QianfanDataSource)

        log_info("create a new dataset group and dataset")
        new_data_source = QianfanDataSource.create_bare_dataset(
            name=f"{origin_data_source.name}_etl_result_set_{uuid.uuid4()}",
            template_type=origin_data_source.template_type,
            storage_type=origin_data_source.storage_type,
            storage_id=origin_data_source.storage_id,
            storage_path=origin_data_source.storage_path,
            ak=origin_data_source.ak,
            sk=origin_data_source.sk,
        )

        log_debug(
            f"new dataset id: {new_data_source.id} , and name: {new_data_source.name}"
        )
        log_info("new dataset group and dataset created, start creating etl task")

        Data.create_dataset_etl_task(
            source_dataset_id=origin_data_source.id,
            destination_dataset_id=new_data_source.id,
            operations=operator_dict,
        )

        etl_result = Data.get_dataset_etl_task_list()["result"]
        if etl_result.get("processingCount", 0) == 0:
            message = "get empty etl task list after creating an etl task"
            log_error(message)
            raise ValueError(message)

        etl_list = etl_result.get("items", [])
        etl_id: Optional[int] = None
        for task in etl_list:
            if (
                task["sourceDatasetId"] == origin_data_source.id
                and task["destDatasetId"] == new_data_source.id
            ):
                etl_id = task["etlId"]
                break

        if etl_id is None:
            message = "can't find matched processing etl task"
            log_error(message)
            raise ValueError(message)

        log_info(f"created etl task id: {etl_id}")
        return etl_id, new_data_source.id

    # 因为要针对数据集在千帆上的在线处理，所以需要加一些额外的处理逻辑。
    # 例如通过平台的 API 发起数据清洗任务
    def online_data_process(self, operators: List[QianfanOperator]) -> Dict[str, Any]:
        """
        create an online ETL task on qianfan
        not available currently

        Args:
            operators (List[QianfanOperator]): operators applied to ETL task

        Returns:
            Dict[str, Any]: ETL task info, contains 3 field:
                is_succeeded (bool): whether ETL task succeed
                etl_task_id (Optional[int]): etl task id, only
                    exists when etl task is created successfully
                new_dataset_id (Optional[int]): dataset id which
                    stores data after etl, only exists when etl
                    task is succeeded
        """

        ret_dict: Dict[str, Any] = {"is_succeeded": False}

        if not self._is_dataset_located_in_qianfan():
            # 如果数据集不是已经在千帆上，则直接失败，因为被处理的数据集必须在云上
            # 目前不支持自动先将本地数据集上传到云端，处理完成后再同步回本地这种操作。
            log_warn("can't process a non-qianfan dataset on qianfan")
            return ret_dict

        if not self._is_dataset_generic_text():
            # 如果数据集不是泛文本，也不支持清洗
            log_warn("can't process qianfan dataset which isn't GenericText type")
            return ret_dict

        operator_dict: Dict[str, List[Dict[str, Any]]] = {}
        for operator in operators:
            attr_dict = operator.model_dump()
            attr_dict.pop("operator_name")
            attr_dict.pop("operator_type")

            elem_dict = {"name": operator.operator_name, "args": attr_dict}

            operator_type = operator.operator_type
            if operator_type not in operator_dict:
                operator_dict[operator_type] = []

            operator_dict[operator_type].append(elem_dict)

        log_debug(f"operator args dict: {operator_dict}")
        log_info("start to creating an etl task")

        etl_id, new_dataset_id = self._create_a_dataset_etl_task(operator_dict)

        log_debug(f"get etl id {etl_id}")
        log_info("creating etl task successfully")

        ret_dict["etl_task_id"] = etl_id

        while True:
            sleep(get_config().ETL_STATUS_POLLING_INTERVAL)
            result = Data.get_dataset_etl_task_info(etl_id)["result"]
            if result["processStatus"] == ETLTaskStatus.Finished.value:
                log_info(f"data etl task {etl_id} succeeded")
                ret_dict["is_succeeded"] = True
                ret_dict["new_dataset_id"] = new_dataset_id
                return ret_dict
            if result["processStatus"] == ETLTaskStatus.Running.value:
                log_info(f"data etl task {etl_id} running, keep polling")
                continue
            if result["processStatus"] == ETLTaskStatus.Paused.value:
                log_warn(f"etl task {etl_id} paused")
                continue
            if result["processStatus"] in [
                ETLTaskStatus.Failed.value,
                ETLTaskStatus.Interrupted.value,
            ]:
                log_warn(
                    f"etl task {etl_id} terminated with status code:"
                    f" {result['processStatus']}"
                )
                return ret_dict
        log_error("should not reach there")
        return ret_dict

    # -------------------- Processable 相关 ----------------
    # 直接调用 Table 对象的接口方法
    # 这些接口不支持用在云端数据集上
    @_online_except_decorator
    def map(self, op: Callable[[Any], Any]) -> Self:
        """
        map on dataset

        Args:
            op (Callable[[Any], Any]): handler used to map

        Returns:
            Self: Dataset itself
        """
        return super().map(op)

    @_online_except_decorator
    def filter(self, op: Callable[[Any], bool]) -> Self:
        """
        filter on dataset

        Args:
            op (Callable[[Any], bool]): handler used to filter

        Returns:
            Self: Dataset itself
        """
        return super().filter(op)

    @_online_except_decorator
    def delete(self, index: Union[int, str]) -> Self:
        """
        delete an element from dataset

        Args:
            index (Union[int, str]): element index to delete

        Returns:
            Self: Dataset itself
        """
        return super().delete(index)

    # 但是在云上数据集追加数据未来可以支持，本质是向数据集中导入新数据。
    # 目前不做修改，等待接口 ready
    @_online_except_decorator
    def append(self, elem: Any) -> Self:
        """
        append an element to dataset

        Args:
            elem (Union[List[Dict], Tuple[Dict], Dict]): elements added to dataset
        Returns:
            Self: Dataset itself
        """
        return super().append(elem)

    def list(
        self,
        by: Optional[Union[slice, int, str, Sequence[int], Sequence[str]]] = None,
        **kwargs: Any,
    ) -> Any:
        """
        get element(s) from dataset

        Args:
            by (Optional[Union[slice, int, Sequence[int]]]):
                index or indices for elements, default to None, in which case
                return a python list of dataset row
        Returns:
            Any: dataset row list
        """
        if not self._is_dataset_located_in_qianfan():
            log_info(f"list local dataset data by {by}")
            return super().list(by)
        else:
            assert isinstance(self.inner_data_source_cache, QianfanDataSource)
            log_info(f"list qianfan dataset data by {by}")

            if isinstance(by, str):
                message = "can't get entity by string from qianfan"
                log_error(message)
                raise ValueError(message)
            elif isinstance(by, (list, tuple)):
                message = "can't get entity by sequence from qianfan"
                log_error(message)
                raise ValueError(message)

            args = {"dataset_id": self.inner_data_source_cache.id}

            if isinstance(by, int):
                args["offset"] = by
                args["page_size"] = 1
            elif isinstance(by, slice):
                args["offset"] = by.start
                args["page_size"] = by.stop - by.start

            log_debug(f"request qianfan dataset list args: {args}")
            resp = Data.list_all_entity_in_dataset(**{**kwargs, **args})["result"][
                "items"
            ]
            log_info("received dataset list from qianfan dataset")
            log_debug(f"request qianfan dataset list response items: {resp}")
            result = [
                {"entity_id": record["id"], "entity_url": record["url"]}
                for record in resp
            ]

            for elem in result:
                for i in range(get_config().GET_ENTITY_CONTENT_FAILED_RETRY_TIMES):
                    log_info(
                        f"retrieve single entity from {elem['entity_url']} in try {i}"
                    )
                    resp = requests.get(elem["entity_url"])
                    if resp.status_code == 200:
                        break
                    log_warn(f"request url {elem['entity_url']} failed, retry")

                if resp.status_code != 200:
                    message = (
                        f"request content of entity {elem['entity_id']} from"
                        f" {elem['entity_url']} failed"
                    )
                    log_error(message)
                    raise RequestError(message)

                log_info(
                    f"retrieve single entity from {elem['entity_url']} succeeded, with"
                    f" content: {resp.text}"
                )
                elem.pop("entity_url")
                elem["entity_content"] = resp.text

            return result

    def __getitem__(self, key: Any) -> Any:
        if (
            isinstance(key, int)
            or isinstance(key, slice)
            or (isinstance(key, (list, tuple)) and key and isinstance(key[0], int))
        ):
            return self.list(key)
        else:
            return self.col_list(key)

    def __delitem__(self, key: Any) -> None:
        if isinstance(key, int):
            self.delete(key)
        elif isinstance(key, str):
            self.col_delete(key)
        else:
            err_msg = f"unsupported key type for deleting: {type(key)}"
            log_error(err_msg)
            raise TypeError(err_msg)

    # 列操作集
    @_online_except_decorator
    def col_map(self, op: Callable[[Any], Any]) -> Self:
        """
        map on dataset's column

        Args:
            op (Callable[[Any], Any]): handler used to map

        Returns:
            Self: Dataset itself
        """
        return super().col_map(op)

    @_online_except_decorator
    def col_filter(self, op: Callable[[Any], bool]) -> Self:
        """
        filter on dataset's column

        Args:
            op (Callable[[Any], bool]): handler used to filter

        Returns:
            Self: Dataset itself
        """
        return super().col_filter(op)

    @_online_except_decorator
    def col_delete(self, index: Union[int, str]) -> Self:
        """
        delete an column from dataset

        Args:
            index (str): column name to delete

        Returns:
            Self: Dataset itself
        """
        return super().col_delete(index)

    @_online_except_decorator
    def col_append(self, elem: Any) -> Self:
        """
        append a row to dataset

        Args:
            elem (Dict[str, List]): dict containing element added to dataset
                must has column name "name" and column data list "data"
        Returns:
            Self: Dataset itself
        """
        return super().col_append(elem)

    # 等待接口 ready 才能对云端数据集做展示
    @_online_except_decorator
    def col_list(
        self,
        by: Optional[
            Union[slice, int, str, List[int], Tuple[int], List[str], Tuple[str]]
        ] = None,
    ) -> Any:
        """
        get column(s) from dataset

        Args:
            by (Optional[Union[int, str, Sequence[int], Sequence[str]]]):
                index or indices for columns, default to None, in which case
                return a python list of dataset column
        Returns:
            Any: dataset column list
        """
        return super().col_list(by)

    @_online_except_decorator
    def col_names(self) -> List[str]:
        """
        get column name list

        Returns:
            List[str]: column name list
        """
        return super().col_names()
