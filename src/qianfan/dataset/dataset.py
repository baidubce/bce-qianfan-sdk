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
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

import pyarrow.json
from typing_extensions import Self

from qianfan.dataset.consts import QianfanDefaultColumnNameForNestedTable
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
from qianfan.errors import ValidationError
from qianfan.resources.console.consts import DataTemplateType
from qianfan.utils import log_debug, log_error, log_info


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
            data_py_rep = json.loads(
                str_content.replace("\r", "\\r").replace("\n", "\\n")
            )
            # 如果导入的是一个字典，则需要转换成列表才能被读取
            if not isinstance(data_py_rep, list):
                data_py_rep = [data_py_rep]
            pyarrow_table = pyarrow.Table.from_pylist(data_py_rep)
        elif format_type == FormatType.Jsonl:
            json_data_list = [
                json.loads(line.replace("\r", "\\r").replace("\n", "\\n"))
                for line in str_content.split("\n")
                if line
            ]
            if not json_data_list:
                raise ValueError("no data in jsonline file")
            if isinstance(json_data_list[0], list):
                # 如果读取的是一个 Json 列表的列表，则必须嵌套存储
                # 因为 Pyarrow Table 并不适合存储列表形式的数据
                # 行与列的处理能力暂不支持嵌套存储的数据集
                # 后续开发相关支持，将此时的数据集底层实现
                # 更换为 pyarrow.Array
                json_data_dict = {
                    QianfanDefaultColumnNameForNestedTable: json_data_list
                }
                pyarrow_table = pyarrow.Table.from_pydict(json_data_dict)
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

            # 如果是 Jsonl，则需要处理嵌套的情况
            column_names = self.inner_table.column_names
            if (
                len(column_names) == 1
                and QianfanDefaultColumnNameForNestedTable == column_names[0]
            ):
                compo_list = self.inner_table.to_pydict()[
                    QianfanDefaultColumnNameForNestedTable
                ]
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

    # 因为要针对数据集在千帆上的在线处理，所以需要加一些额外的处理逻辑。
    # 例如通过平台的 API 发起数据清洗任务
    def online_data_process(self, operators: List[QianfanOperator]) -> bool:
        """
        create a online ETL task on qianfan
        not available currently

        Args:
            operators (List[QianfanOperator]): operators applied to ETL task

        Returns:
            bool: is ETL task succeeded
        """
        if not self._is_dataset_located_in_qianfan():
            # 如果数据集不是已经在千帆上，则直接失败，因为被处理的数据集必须在云上
            # 目前不支持自动先将本地数据集上传到云端，处理完成后再同步回本地这种操作。
            return False

        # 这里根据 operators 来填充参数，然后发起数据清洗，最后将任务处理结果返回。
        # 目前没有实现相关接口，直接抛出 False
        return False

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

    # 等待接口 ready 才能对云端数据集做展示
    @_online_except_decorator
    def list(
        self,
        by: Optional[
            Union[slice, int, str, List[int], Tuple[int], List[str], Tuple[str]]
        ] = None,
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
        return super().list(by)

    def __getitem__(self, key: Any) -> Any:
        return self.list(key)

    def __delitem__(self, key: Any) -> None:
        self.delete(key)

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
