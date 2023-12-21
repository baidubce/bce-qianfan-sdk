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
import codecs
import csv
import functools
import io
import json
import os
import time
from copy import deepcopy
from time import sleep
from typing import Any, Callable, Dict, Iterator, List, Optional, Sequence, Tuple, Union
from zipfile import ZipFile

import pyarrow.json
import requests
from pyarrow import Table as PyarrowTable
from pyarrow import csv as pyarrow_csv
from typing_extensions import Self

from qianfan import ChatCompletion, Completion, QfResponse, QfRole, get_config
from qianfan.components import Prompt
from qianfan.dataset.consts import (
    QianfanDataGroupColumnName,
    QianfanDatasetPackColumnName,
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
from qianfan.dataset.utils import (
    _construct_table_from_nest_sequence,
)
from qianfan.errors import QianfanError, RequestError, ValidationError
from qianfan.resources import Data, Model
from qianfan.resources.console.consts import (
    DataTemplateType,
    ETLTaskStatus,
    EvaluationTaskStatus,
)
from qianfan.utils import log_debug, log_error, log_info, log_warn
from qianfan.utils.utils import generate_letter_num_random_id


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

    def __init__(
        self,
        inner_table: PyarrowTable,
        inner_data_source_cache: Optional[DataSource] = None,
        inner_schema_cache: Optional[Schema] = None,
        input_columns: Optional[List[str]] = None,
        reference_column: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        """
        Init a Dataset Object

        Args:
            inner_table (PyarrowTable):
                a pyarrow.Table object wrapped by Table
            inner_data_source_cache (Optional[DataSource]):
                a data source cache where the dataset was loaded from
            inner_schema_cache (Optional[Schema]):
                schema cache used when dataset was loaded
            input_columns (Optional[List[str]]):
                which columns should be extracted as inputs
            reference_column (Optional[str]):
                which column should be extracted as reference
            **kwargs (Any):
                optional arguments
        """
        super().__init__(inner_table)

        # 内部的数据源对象，在 load 时被指定
        self.inner_data_source_cache: Optional[DataSource] = inner_data_source_cache

        # schema 对象的缓存，在 load 时被指定
        self.inner_schema_cache: Optional[Schema] = inner_schema_cache

        # 输入列的列名列表
        self.input_columns = input_columns

        # 预期结果列的列名
        self.reference_column = reference_column

    @classmethod
    def _from_source(
        cls,
        source: DataSource,
        schema: Optional[Schema],
        is_a_text_file_an_entry: bool = False,
        **kwargs: Any,
    ) -> "Dataset":
        """
        内部封装的从数据源导出字节流并构建数据集的方法
        当设置了 is_a_text_file_an_entry = True，
        且是读取 txt 格式的文件夹数据，则此时将
        一个文件中的所有文本作为一条数据，而不是
        按照一行文本作为一条数据
        """
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
        content = source.fetch(**kwargs)
        format_type = source.format_type()

        log_debug(
            f"content (type: {format_type}) fetched from data source: \n{content}"
        )

        if isinstance(content, str):
            content = [content]

        if format_type == FormatType.Json:
            json_dict_list: List[Dict[str, Any]] = []
            for str_content in content:
                data_py_rep = json.loads(str_content)
                # 如果导入的是一个字典，则需要转换成列表才能被读取
                if not isinstance(data_py_rep, list):
                    data_py_rep = [data_py_rep]
                json_dict_list.extend(data_py_rep)
            pyarrow_table = pyarrow.Table.from_pylist(json_dict_list)
        elif format_type == FormatType.Jsonl:
            json_data_list: List[Dict[str, Any]] = []
            for str_content in content:
                tmp_list = [
                    json.loads(line) for line in str_content.split("\n") if line
                ]
                json_data_list.extend(tmp_list)

            if not json_data_list:
                raise ValueError("no data in jsonline file")
            if isinstance(json_data_list[0], list):
                pyarrow_table = _construct_table_from_nest_sequence(json_data_list)
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
            csv_data: List[Dict[str, Any]] = []
            for str_content in content:
                string_buffer = io.StringIO(
                    str_content.strip(codecs.BOM_UTF8.decode(encoding="utf-8"))
                )
                tmp_data = [row for row in csv.DictReader(string_buffer)]
                csv_data.extend(tmp_data)

            pyarrow_table = pyarrow.Table.from_pylist(csv_data)
        elif format_type == FormatType.Text:
            # 如果是纯文本，则放置在 prompt 一列下
            line_data: List[str] = []
            for str_content in content:
                # 如果指定了按照文件为粒度进行读取，
                # 则此时一行数据就是一个文本中的所有文件
                if is_a_text_file_an_entry:
                    line_data.append(str_content)
                else:
                    line_data.extend(str_content.split("\n"))
            pyarrow_table = pyarrow.Table.from_pydict(
                {QianfanDatasetPackColumnName: line_data}
            )
        else:
            error = ValueError(f"unknown format type: {format_type}")
            log_error(str(error))
            raise error

        return cls(
            inner_table=pyarrow_table.combine_chunks(),  # 性能优化，combine_chunks()
            inner_data_source_cache=source,
            inner_schema_cache=schema,
            **kwargs,
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

            # 如果是 Jsonl，则需要处理所有可能的情况
            if self.is_dataset_packed():
                log_info("enter packed deserialization logic")
                data_list = self.col_list(QianfanDatasetPackColumnName)[
                    QianfanDatasetPackColumnName
                ]

                for entity in data_list:
                    list_of_json.append(json.dumps(entity, ensure_ascii=False))
            elif self.is_dataset_grouped():
                log_info("enter grouped deserialization logic")
                self._squash_group_number()
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
                log_info("enter qianfan deserialization logic")
                dict_list = self.inner_table.to_pylist()
                for elem in dict_list:
                    list_of_json.append(f"[{json.dumps(elem, ensure_ascii=False)}]")
            else:
                log_info("enter else logic")
                dict_list = self.inner_table.to_pylist()
                for elem in dict_list:
                    list_of_json.append(json.dumps(elem, ensure_ascii=False))
            return source.save("\n".join(list_of_json), **kwargs)

        elif format_type == FormatType.Csv:
            bytes_stream_buffer = io.BytesIO()
            bytes_stream_buffer.write(codecs.BOM_UTF8)
            pyarrow_csv.write_csv(self.inner_table, bytes_stream_buffer)
            return source.save(bytes_stream_buffer.getvalue().decode("utf-8"), **kwargs)

        elif format_type == FormatType.Text:
            # 导出为纯文本时，列的数量不可大于 1
            if self.column_number() > 1:
                error = ValueError(
                    "cannot export dataset to pure text if the number of column is"
                    " greater than 1"
                )
                log_error(str(error))
                raise error
            result_list = list(self.inner_table.to_pydict().values())[0]

            if isinstance(source, QianfanDataSource):
                tmp_zip_file_name = (
                    f"tmp_zip_file_{generate_letter_num_random_id()}.zip"
                )

                try:
                    with ZipFile(tmp_zip_file_name, mode="w") as tmp_zip:
                        for i in range(len(result_list)):
                            tmp_zip.writestr(
                                f"generic_text_file_{i}.txt", data=result_list[i]
                            )

                    result = source.save(zip_file_path=tmp_zip_file_name, **kwargs)
                    return result
                finally:
                    if os.path.exists(tmp_zip_file_name):
                        os.remove(tmp_zip_file_name)

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
        bos_load_args: Optional[Dict[str, Any]] = None,
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

        if bos_load_args:
            log_info(
                "construct a new qianfan data source from bos loading:"
                f" {bos_load_args}, with args: {kwargs}"
            )
            return QianfanDataSource.create_from_bos_file(**bos_load_args)

        log_info("no datasource was constructed")
        return None

    def _set_qianfan_default_io_column(self) -> None:
        cache_data_source = self.inner_data_source_cache
        if not isinstance(cache_data_source, QianfanDataSource):
            return

        if cache_data_source.template_type in [
            DataTemplateType.NonSortedConversation,
            DataTemplateType.SortedConversation,
            DataTemplateType.QuerySet,
        ]:
            self.input_columns = ["prompt"]

        if cache_data_source.template_type in [
            DataTemplateType.NonSortedConversation,
            DataTemplateType.SortedConversation,
        ]:
            self.reference_column = "reference"

    @classmethod
    def load(
        cls,
        source: Optional[DataSource] = None,
        data_file: Optional[str] = None,
        qianfan_dataset_id: Optional[int] = None,
        bos_load_args: Optional[Dict[str, Any]] = None,
        huggingface_dataset: Optional[Any] = None,
        schema: Optional[Schema] = None,
        organize_data_as_group: bool = False,
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
            bos_load_args: (Optional[Dict[str, Any]]):
                create a dataset and import initial dataset content
                from args
            huggingface_dataset (Optional[Dict[str, Any], Any]):
                Huggingface dataset object, only support
                DatasetDict and Dataset of Huggingface datasets.
            schema (Optional[Schema]):
                schema used to validate loaded data, default to None
            organize_data_as_group (bool):
                only available when data source's format is
                FormatType.Jsonl. Indicates whether
                organize data within dataset in group format,
                default to False, and when it's True, the
                default format will be a group-based 2D structure.
            **kwargs (Any): optional arguments

        Returns:
            Dataset: a dataset instance
        """

        if not source:
            if huggingface_dataset is not None:
                log_info("construct dataset from huggingface dataset")
                if not hasattr(huggingface_dataset, "data"):
                    err_msg = (
                        "huggingface_dataset should be either DatasetDict or Dataset of"
                        " Huggingface datasets. "
                    )
                    log_error(err_msg)
                    raise ValueError(log_error)

                data = huggingface_dataset.data
                if isinstance(data, dict):
                    log_info("construct from huggingface DatasetDict")
                    pyarrow_table = pyarrow.concat_tables(
                        [ds.table for ds in data.values()]
                    )
                    return cls.create_from_pyarrow_table(pyarrow_table.combine_chunks())
                elif hasattr(data, "table"):
                    log_info("construct from huggingface Dataset")
                    return cls.create_from_pyarrow_table(data.table.combine_chunks())

                err_msg = (
                    f"get unsupported data type {type(data)} from huggingface dataset"
                )
                log_error(err_msg)
                raise TypeError(err_msg)

            log_info("no data source was provided, construct")
            source = cls._from_args_to_source(
                data_file=data_file,
                qianfan_dataset_id=qianfan_dataset_id,
                bos_load_args=bos_load_args,
                **kwargs,
            )

        # 从数据源开始构建对象
        if not source:
            err_msg = "no data source or other arguments provided for loading"
            log_error(err_msg)
            raise ValueError(err_msg)

        table = cls._from_source(source, schema, **kwargs)

        # 校验
        if schema and not schema.validate(table):
            error = ValidationError("validate failed when initialize dataset")
            log_error(str(error))
            raise error

        table._set_qianfan_default_io_column()

        if table.is_dataset_grouped() and not organize_data_as_group:
            table.pack()

        return table

    def save(
        self,
        destination: Optional[DataSource] = None,
        data_file: Optional[str] = None,
        qianfan_dataset_id: Optional[int] = None,
        qianfan_dataset_create_args: Optional[Dict[str, Any]] = None,
        schema: Optional[Schema] = None,
        replace_source: bool = False,
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
            schema: (Optional[Schema]):
                schema used to validate before exporting data, default to None
            replace_source: (bool):
                if replace the original source, default to False
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
                is_download_to_local=False,
                **kwargs,
            )

        # 获取数据源参数
        source = destination if destination else self.inner_data_source_cache
        if not source:
            err_msg = "no data source or other arguments provided for saving"
            log_error(err_msg)
            raise ValueError(err_msg)

        # 首先检查是否有传入 schema 或者已经默认有了 schema
        schema = schema if schema else self.inner_schema_cache
        # 如果导出的数据源是千帆，则强制构造 schema 进行检查，优先级最高
        if isinstance(source, QianfanDataSource):
            # 一个方法从 source 中抽取 schema 信息
            schema = _get_qianfan_schema(source)

        # 校验
        if schema and not schema.validate(self):
            error = ValidationError("validate failed when save dataset")
            log_error(str(error))
            raise error

        if isinstance(source, QianfanDataSource):
            assert isinstance(schema, QianfanSchema)
            kwargs["is_annotated"] = schema.is_annotated

        # 开始写入数据
        res = self._to_source(source, **kwargs)  # noqa
        if res and replace_source:
            self.inner_data_source_cache = source
        return res

    @classmethod
    def create_from_pyobj(
        cls,
        data: Union[List[Dict[str, Any]], Dict[str, List]],
        schema: Optional[Schema] = None,
        **kwargs: Any,
    ) -> "Dataset":
        """
        create a dataset from python dict or list

        Args:
            data (Union[List[Dict[str, Any]], Dict[str, List]]):
                python object used to create dataset。
            schema (Optional[Schema]):
                schema used to validate before exporting data, default to None
            **kwargs (Any):
                optional arguments

        Returns:
            Dataset: a dataset instance
        """
        if isinstance(data, list):
            return cls(
                inner_table=pyarrow.Table.from_pylist(data).combine_chunks(),
                inner_schema_cache=schema,
                **kwargs,
            )
        else:
            return cls(
                inner_table=pyarrow.Table.from_pydict(data).combine_chunks(),
                inner_schema_cache=schema,
                **kwargs,
            )

    @classmethod
    def create_from_pyarrow_table(
        cls,
        table: pyarrow.Table,
        schema: Optional[Schema] = None,
        **kwargs: Any,
    ) -> "Dataset":
        """
        create a dataset from pyarrow table

        Args:
            table (pyarrow):
                pyarrow table object used to create dataset。
            schema (Optional[Schema]):
                schema used to validate before exporting data, default to None
            **kwargs (Any):
                optional arguments

        Returns:
            Dataset: a dataset instance
        """
        return cls(
            inner_table=table.combine_chunks(),
            inner_schema_cache=schema,
            **kwargs,
        )

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

    def is_dataset_located_in_qianfan(self) -> bool:
        """
        tell whether current dataset is cloud-based dataset

        Returns:
            bool: whether current dataset is cloud-based dataset
        """
        return self._is_dataset_located_in_qianfan()

    def is_dataset_generic_text(self) -> bool:
        """
        tell whether current dataset is generic text dataset

        Returns:
            bool: whether current dataset is generic text dataset
        """
        return self._is_dataset_generic_text()

    def _create_a_dataset_etl_task(
        self, operator_dict: Dict[str, List[Dict[str, Any]]]
    ) -> Tuple[int, int]:
        origin_data_source = self.inner_data_source_cache
        assert isinstance(origin_data_source, QianfanDataSource)

        log_info("create a new dataset group and dataset")
        new_data_source = QianfanDataSource.create_bare_dataset(
            name=f"etl_result_set_{generate_letter_num_random_id()}",
            template_type=origin_data_source.template_type,
            storage_type=origin_data_source.storage_type,
            storage_id=origin_data_source.storage_id,
            storage_path=origin_data_source.storage_raw_path,
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

    def start_online_data_process_task(self, operators: List[QianfanOperator]) -> int:
        """
        create an online ETL task on qianfan

        Args:
            operators (List[QianfanOperator]): operators applied to ETL task

        Returns:
            int: etl task id
        """

        if not self._is_dataset_located_in_qianfan():
            # 如果数据集不是已经在千帆上，则直接失败，因为被处理的数据集必须在云上
            # 目前不支持自动先将本地数据集上传到云端，处理完成后再同步回本地这种操作。
            err_msg = "can't process a non-qianfan dataset on qianfan"
            log_error(err_msg)
            raise ValueError(err_msg)

        if not self._is_dataset_generic_text():
            # 如果数据集不是泛文本，也不支持清洗
            err_msg = "can't process qianfan dataset which isn't GenericText type"
            log_error(err_msg)
            raise ValueError(err_msg)

        operator_dict: Dict[str, List[Dict[str, Any]]] = {
            "clean": [],
            "filter": [],
            "deduplication": [],
            "desensitization": [],
        }
        for operator in operators:
            attr_dict = operator.model_dump()
            attr_dict.pop("operator_name")
            attr_dict.pop("operator_type")

            elem_dict = {"name": operator.operator_name, "args": attr_dict}

            operator_type = operator.operator_type
            operator_dict[operator_type].append(elem_dict)

        log_debug(f"operator args dict: {operator_dict}")
        log_info("start to creating an etl task")

        etl_id = self._create_a_dataset_etl_task(operator_dict)[0]
        return etl_id

    @staticmethod
    def check_online_data_process_result(etl_id: int) -> Optional[Union[bool, int]]:
        """
        check etl task result using etl task id

        Args:
            etl_id (int):
                etl task id
        Returns:
            Optional[Union[bool, int]]: return None when task is still on processing.
                return False if task failed and return dataset id which contains data
                after clean
        """
        result = Data.get_dataset_etl_task_info(etl_id)["result"]
        if result["processStatus"] == ETLTaskStatus.Finished.value:
            log_info(f"data etl task {etl_id} succeeded")
            return result["destDatasetId"]
        if result["processStatus"] == ETLTaskStatus.Running.value:
            log_info(f"data etl task {etl_id} running")
            return None
        if result["processStatus"] == ETLTaskStatus.Paused.value:
            log_warn(f"etl task {etl_id} paused")
            return None
        if result["processStatus"] in [
            ETLTaskStatus.Failed.value,
            ETLTaskStatus.Interrupted.value,
        ]:
            log_warn(
                f"etl task {etl_id} terminated with status code:"
                f" {result['processStatus']}"
            )
            return False

        return False

    def online_data_process(self, operators: List[QianfanOperator]) -> Dict[str, Any]:
        """
        create an online ETL task on qianfan

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

        etl_id = self.start_online_data_process_task(operators)

        log_debug(f"get etl id {etl_id}")
        log_info("creating etl task successfully")

        ret_dict: Dict[str, Any] = {"is_succeeded": False, "etl_task_id": etl_id}

        while True:
            sleep(get_config().ETL_STATUS_POLLING_INTERVAL)
            result = self.check_online_data_process_result(etl_id)
            if result is None:
                continue
            if not result:
                return ret_dict
            else:
                ret_dict["new_dataset_id"] = result
                ret_dict["is_succeeded"] = True
                break

        return ret_dict

    def add_default_group_column(self) -> Self:
        """
        add "_group" column to Dataset, the value
        in "_group" column are sequential incremental

        Returns:
            Self: Dataset itself
        """

        if QianfanDataGroupColumnName in self.col_names():
            # 如果已经存在，则不做任何处理
            return self

        return self.col_append(
            {"name": QianfanDataGroupColumnName, "data": list(range(self.row_number()))}
        )

    def delete_group_column(self) -> Self:
        """
        remove "_group" column from Dataset

        Returns:
            Self: Dataset itself
        """

        if QianfanDataGroupColumnName not in self.col_names():
            return self

        return self.col_delete(QianfanDataGroupColumnName)

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
    def append(
        self, elem: Any, add_new_group: bool = False, is_grouped: bool = True
    ) -> Self:
        """
        append element(s) to dataset

        Args:
            elem (Union[List[List[Dict]], List[Dict], Tuple[Dict], Dict]):
                Elements added to dataset
            add_new_group (bool):
                Whether elem has a new group id.
                Only used when dataset is grouped.
            is_grouped (bool):
                Are element in elem in same group.
                Only used when dataset is grouped and elem is Sequence
                and add_new_group was set True.
                Default to True, all elements
                will be in same group.
                If it's True, each element will have
                sequential incremental group id from last
                available group id.
        Returns:
            Self: Dataset itself
        """
        return super().append(elem, add_new_group, is_grouped)

    @_online_except_decorator
    def insert(
        self,
        elem: Any,
        index: Any,
        group_id: int = -1,
        add_new_group: bool = False,
        is_grouped: bool = True,
    ) -> Self:
        """
        insert element(s) to dataset

        Args:
            elem (Union[List[List[Dict]], List[Dict], Tuple[Dict], Dict]):
                Elements added to dataset
            index (int): where to insert element(s)
            group_id (int):
                which group id you want to apply to new element(s).
                Default to -1, which means let group id be automatically
                inferred from table.
            add_new_group (bool):
                Whether elem has a new group id.
                Only used when dataset is grouped
                and group_id is -1
            is_grouped (bool):
                Are element in elem in same group.
                Only used when dataset is grouped and elem is Sequence
                and add_new_group was set True.
                Default to True, all elements
                will be in same group.
                If it's True, each element will have
                sequential incremental group id from last
                available group id.
        Returns:
            Self: Dataset itself
        """
        return super().insert(elem, index, add_new_group, is_grouped)

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

    def row_number(self) -> int:
        if (
            isinstance(self.inner_data_source_cache, QianfanDataSource)
            and not self.inner_data_source_cache.download_when_init
        ):
            return Data.get_dataset_info(self.inner_data_source_cache.id)["result"][
                "versionInfo"
            ]["entityCount"]
        else:
            return super().row_number()

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
                must have column name "name" and column data list "data"
        Returns:
            Self: Dataset itself
        """
        return super().col_append(elem)

    @_online_except_decorator
    def col_insert(self, elem: Any, index: Any) -> Self:
        """
        append a row to dataset

        Args:
            elem (Dict[str, List]): dict containing element added to dataset
                must has column name "name" and column data list "data"
            index (int): where to insert new column
        Returns:
            Self: Dataset itself
        """
        return super().col_insert(elem, index)

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

    @_online_except_decorator
    def col_renames(self, new_names: List[str]) -> Self:
        """
        rename all dataset column

        Args:
            new_names (List[str]): All new names for columns
        Returns:
            Self: A brand-new Dataset with new name
        """
        return super().col_renames(new_names)

    @property
    @_online_except_decorator
    def get_reference_data(self) -> List[Any]:
        """
        get reference data in dataset

        Returns:
            List[Any]: list of output data column
        """
        return self.col_list(self.reference_column)[self.reference_column]

    @property
    @_online_except_decorator
    def get_input_data(self) -> Dict[str, List[Any]]:
        """
        get input columns data in dataset

        Returns:
            Dict[str, List[Any]]: a dict
                which indicates the "column name-column data" pairs
        """
        return self[self.input_columns]

    def test_using_llm(
        self,
        model_id: Optional[int] = None,
        model_version_id: Optional[int] = None,
        service_model: Optional[str] = None,
        service_endpoint: Optional[str] = None,
        is_chat_service: bool = False,
        **kwargs: Any,
    ) -> "Dataset":
        """
        using arguments to init an llm instance
        and get output on current dataset from it
        set only model arguments our service arguments to instantiating

        Args:
            model_id (Optional[int]):
                id of your own model, default to None
            model_version_id (Optional[int]):
                version id of your own model, default to None
            service_model (Optional[str]):
                name of model you want to use as service, default to None
            service_endpoint (Optional[str]):
                endpoint of service, default to None
            is_chat_service (bool):
                the service type of service, default to True.
                Service will be Completion if False
            **kwargs (Any):
                optional argument dict

        Returns:
            Dataset: A dataset contains inputs, reference outputs and llm outputs
        """

        if model_id and model_version_id:
            return self._batch_inference_on_model(model_id, model_version_id, **kwargs)
        elif service_model or service_endpoint:
            return self._batch_inference_on_service(
                service_model, service_endpoint, is_chat_service, **kwargs
            )
        else:
            err_msg = "no sufficient argument has been passed"
            log_error(err_msg)
            raise ValueError(err_msg)

    def _batch_inference_on_model(
        self, model_id: int, model_version_id: int, **kwargs: Any
    ) -> "Dataset":
        """
        create batch run using specific dataset on qianfan
        by evaluation ability of platform

        Parameters:
            model_id (int):
                id of your own model, default to None
            model_version_id (int):
                version id of your own model, default to None
            **kwargs (Any):
                Arbitrary keyword arguments

        Returns:
            Dataset: batch result contained in dataset
        """

        if not self.is_dataset_located_in_qianfan():
            err_msg = "can't start a batch run task on non-qianfan dataset"
            log_error(err_msg)
            raise ValueError(err_msg)

        if self.is_dataset_generic_text():
            err_msg = "can't start a batch run task on generic text dataset"
            log_error(err_msg)
            raise ValueError(err_msg)

        qianfan_data_source = self.inner_data_source_cache
        assert isinstance(qianfan_data_source, QianfanDataSource)

        log_info("start to create evaluation task in model")

        resp = Model.create_evaluation_task(
            name=f"model_run_{generate_letter_num_random_id()}",
            version_info=[
                {
                    "modelId": model_id,
                    "modelVersionId": model_version_id,
                }
            ],
            dataset_id=qianfan_data_source.id,
            eval_config={
                "evalMode": "manual",
                "evaluationDimension": [
                    {"dimension": "满意度"},
                ],
            },
            dataset_name=qianfan_data_source.name,
            **kwargs,
        ).body

        eval_id = resp["result"]["evalId"]

        log_debug(f"create evaluation task in model response: {resp}")
        log_info(f"start to polling status of evaluation task {eval_id}")

        while True:
            eval_info = Model.get_evaluation_info(eval_id)
            eval_state = eval_info["result"]["state"]

            log_debug(f"current evaluation task info: {eval_info}")
            log_info(f"current eval_state: {eval_state}")

            if eval_state not in [
                EvaluationTaskStatus.Pending.value,
                EvaluationTaskStatus.Doing.value,
            ]:
                break
            time.sleep(get_config().BATCH_RUN_STATUS_POLLING_INTERVAL)

        if eval_state not in [
            EvaluationTaskStatus.DoingWithManualBegin,
            EvaluationTaskStatus.Done,
        ]:
            err_msg = f"can't finish evaluation task and failed with state {eval_state}"
            log_error(err_msg)
            raise QianfanError(err_msg)

        result_dataset_id = eval_info["result"]["evalStandardConf"]["resultDatasetId"]
        log_info(f"get result dataset id {result_dataset_id}")

        return Dataset.load(qianfan_dataset_id=result_dataset_id, **kwargs)

    def _batch_inference_on_service(
        self,
        service_model: Optional[str] = None,
        service_endpoint: Optional[str] = None,
        is_chat_service: bool = False,
        system_prompt: str = "",
        **kwargs: Any,
    ) -> "Dataset":
        """
        create batch run using specific dataset on qianfan

        Args:
            service_model (Optional[str]):
                name of model you want to use as service, default to None
            service_endpoint (Optional[str]):
                endpoint of service, default to None
            is_chat_service (bool):
                the service type of service, default to True.
                Service will be Completion if False
            system_prompt (str):
                Optional system text for input using, default to ""
            **kwargs (Any):
                Arbitrary keyword arguments

        Keyword arguments:
            prompt_template (Optional[Prompt]):
                Optional Prompt used as input of llm, default to None.
                Only used when your Service is a Completion service

        Returns:
            Dataset: batch result contained in dataset
        """

        if self.is_dataset_located_in_qianfan():
            err_msg = "can't start a batch run task on qianfan dataset"
            log_error(err_msg)
            raise ValueError(err_msg)

        input_columns = self.input_columns
        if not input_columns:
            err_msg = "no input column has been set"
            log_error(err_msg)
            raise ValueError(err_msg)

        prompt_template: Optional[Prompt] = kwargs.get("prompt_template", None)

        if prompt_template:
            log_info("prompt template detected, start to check template variables")
            for column in input_columns:
                if column not in prompt_template.variables:
                    err_msg = f"input column {column} not in prompt template"
                    log_error(err_msg)
                    raise ValueError(err_msg)

        service: Union[ChatCompletion, Completion]
        if is_chat_service:
            service = ChatCompletion(service_model, service_endpoint)
        else:
            service = Completion(service_model, service_endpoint)

        def _batch_do_on_service(
            service: Union[ChatCompletion, Completion], *args: Any, **kwargs: Any
        ) -> List[str]:
            output_list: List[str] = []
            results = service.batch_do(*args, **kwargs).results()  # noqa
            for idx in range(len(results)):
                result = results[idx]
                if isinstance(result, QfResponse):
                    output_list.append(result.body["result"])
                elif isinstance(result, Exception):
                    log_warn(
                        "an exception has occurred during batch requesting and its"
                        f" result will be empty string. exception: {result}\ninput:"
                        f" {input_str_list[idx]}"
                    )
                    output_list.append("")
                else:
                    result_str = ""
                    for r in result:
                        result_str += r.body["result"]
                    output_list.append(result_str)

            return output_list

        if isinstance(service, Completion):
            input_dict = self.get_input_data

            if self.is_dataset_grouped() or self.is_dataset_packed():
                err_msg = (
                    "can't have a grouped or packed dataset as batch run task dataset"
                    " when service is Completion"
                )
                log_error(err_msg)
                raise TypeError(err_msg)

            input_str_list: List[str] = []

            for i in range(self.row_number()):
                if prompt_template:
                    input_str_list.append(
                        prompt_template.render(
                            **{
                                column_name: input_dict[column_name][i]
                                for column_name in input_columns
                            },
                            **kwargs,
                        )[0]
                    )
                else:
                    input_str_list.append(
                        "\n".join(
                            [
                                input_dict[column_name][i]
                                for column_name in input_columns
                            ]
                        )
                    )

            output_list = _batch_do_on_service(
                service, input_str_list, system=system_prompt, **kwargs
            )
            return Dataset.create_from_pyobj(
                {
                    **input_dict,
                    "input_prompt": input_str_list,
                    "llm_output": output_list,
                },
                input_columns=self.input_columns,
                reference_column=self.reference_column,
            )
        else:

            def _extract_string(data: Union[str, Iterator[str]]) -> str:
                if isinstance(data, str):
                    return data
                elif hasattr(data, "__iter__"):
                    for item in data:
                        return _extract_string(item)
                return ""

            if len(input_columns) > 1:
                err_msg = (
                    "input column list should only have 1 column name when your Service"
                    " is ChatCompletion"
                )
                log_error(err_msg)
                raise TypeError(err_msg)

            reference_column = self.reference_column
            if not reference_column:
                err_msg = "no reference column has been set"
                log_error(err_msg)
                raise ValueError(err_msg)

            input_column = input_columns[0]

            dataset = deepcopy(self)
            if not dataset.is_dataset_grouped() and not dataset.is_dataset_packed():
                dataset.add_default_group_column()

            if dataset.is_dataset_grouped():
                dataset.pack()

            input_chat_list: List[List[Dict[str, Any]]] = []
            for chat in dataset.list():
                input_messages: List[Dict[str, Any]] = []
                for i in range(len(chat)):
                    input_messages.append(
                        {"role": QfRole.User.value, "content": chat[i][input_column]}
                    )
                    if i != len(chat) - 1:
                        input_messages.append(
                            {
                                "role": QfRole.Assistant.value,
                                "content": chat[i][_extract_string(reference_column)],
                            }
                        )

                input_chat_list.append(input_messages)

            output_list = _batch_do_on_service(
                service, input_chat_list, system=system_prompt, **kwargs
            )
            return Dataset.create_from_pyobj(
                {"input_chats": input_chat_list, "llm_output": output_list},
                input_columns=dataset.input_columns,
                reference_column=reference_column,
            )


def _get_qianfan_schema(source: QianfanDataSource) -> Schema:
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
