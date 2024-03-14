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
import functools
from copy import deepcopy
from time import sleep
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple, Union

import pyarrow.json
from pyarrow import Table as PyarrowTable
from typing_extensions import Self

from qianfan import Completion, QfRole, get_config
from qianfan.common import Prompt
from qianfan.dataset.consts import (
    FirstTokenLatencyColumnName,
    LLMOutputColumnName,
    NewInputChatColumnName,
    NewInputPromptColumnName,
    OldReferenceColumnName,
    QianfanDataGroupColumnName,
    QianfanDatasetPackColumnName,
    RequestLatencyColumnName,
)
from qianfan.dataset.data_source import (
    BosDataSource,
    DataSource,
    FileDataSource,
    QianfanDataSource,
)
from qianfan.dataset.data_source.utils import upload_data_from_bos_to_qianfan
from qianfan.dataset.dataset_utils import (
    _async_batch_do_on_service,
    _batch_do_on_service,
    _check_and_generate_service,
    _check_online_data_process_result,
    _create_a_dataset_etl_task,
    _extract_string,
    _get_qianfan_schema,
    _list_cloud_data,
    _start_an_evaluation_task_for_model_batch_inference,
)
from qianfan.dataset.qianfan_data_operators import QianfanOperator
from qianfan.dataset.schema import (
    QianfanSchema,
    Schema,
)
from qianfan.dataset.table import Table
from qianfan.dataset.table_utils import _construct_packed_table_from_nest_sequence
from qianfan.errors import ValidationError
from qianfan.resources import Data, Model
from qianfan.resources.console.consts import (
    DataTemplateType,
)
from qianfan.utils import log_debug, log_error, log_info, log_warn
from qianfan.utils.bos_uploader import BosHelper


# 装饰器，用来阻塞部分对云上数据集（非本地）的操作请求
def _online_except_decorator(func: Callable) -> Callable:
    @functools.wraps(func)
    def inner(dataset: Any, *args: Any, **kwargs: Any) -> Any:
        if isinstance(dataset.inner_data_source_cache, QianfanDataSource) or isinstance(
            dataset.inner_data_source_cache, BosDataSource
        ):  # noqa
            raise Exception(
                "can't do process on dataset "
                f"which is loaded from {type(dataset.inner_data_source_cache)}"
            )  # noqa
        return func(dataset, *args, **kwargs)

    return inner


class Dataset(Table):
    """Dataset"""

    def __init__(
        self,
        inner_table: Optional[PyarrowTable] = None,
        inner_data_source_cache: Optional[DataSource] = None,
        inner_schema_cache: Optional[Schema] = None,
        input_columns: Optional[List[str]] = None,
        reference_column: Optional[str] = None,
        eval_input_column: Optional[str] = None,
        eval_llm_output_column: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        """
        Init a Dataset Object

        Args:
            inner_table (Optional[PyarrowTable]):
                a pyarrow.Table object wrapped by Table or None
            inner_data_source_cache (Optional[DataSource]):
                a data source cache where the dataset was loaded from
            inner_schema_cache (Optional[Schema]):
                schema cache used when dataset was loaded
            input_columns (Optional[List[str]]):
                which columns should be extracted as inputs
            reference_column (Optional[str]):
                which column should be extracted as reference
            eval_input_column (Optional[str]):
                evaluation input column name in dataset
            eval_llm_output_column (Optional[str]):
                llm output column name in dataset for evaluating
            **kwargs (Any):
                optional arguments
        """
        super().__init__(inner_table)

        # 内部的数据源对象，在 load 时被指定
        self.inner_data_source_cache: Optional[DataSource] = inner_data_source_cache

        # schema 对象的缓存，在 load 时被指定
        self.inner_schema_cache: Optional[Schema] = inner_schema_cache

        # 批量推理输入列的列名列表
        self.input_columns = input_columns

        # 批量推理以及评估时的预期结果列的列名
        self.reference_column = reference_column

        # 只运行评估时，评估的输入列的列名
        self.eval_input_column = eval_input_column

        # 只运行评估时，评估的大模型回答列列名
        self.eval_llm_output_column = eval_llm_output_column

    @classmethod
    def _from_source(
        cls,
        source: DataSource,
        schema: Optional[Schema],
        **kwargs: Any,
    ) -> "Dataset":
        """
        内部封装的从数据源导出字节流并构建数据集的方法
        """
        table = source.load(**kwargs)

        # 特判 is_download_to_local 的兼容
        if table is not None and isinstance(source, QianfanDataSource):
            content_path = source.get_cache_content()
            source = FileDataSource(
                path=content_path, file_format=source.format_type(), save_as_folder=True
            )

        return cls(
            inner_table=table,
            inner_data_source_cache=source,
            inner_schema_cache=schema,
            **kwargs,
        )

    def _to_source(self, source: DataSource, **kwargs: Any) -> Optional[PyarrowTable]:
        """内部封装的，将数据集序列化并导出字节流到数据源的方法"""
        # 重置，不然会重复加载
        if isinstance(source, QianfanDataSource):
            source.download_when_init = None

        # 如果是保存到本地
        if isinstance(source, FileDataSource):
            og_table: Table

            if self.inner_table:
                og_table = self
            elif self.inner_data_source_cache:
                pa_table = self.inner_data_source_cache.fetch(**kwargs)
                assert pa_table
                og_table = Table(inner_table=pa_table)
            else:
                err_msg = (
                    "can't get table because both inner_table and"
                    " inner_data_source_cache are empty"
                )
                log_error(err_msg)
                raise ValueError(err_msg)

            # 特判，因为从千帆导出来的数据，格式是一定的，用户乱指定也没有用
            if isinstance(self.inner_data_source_cache, QianfanDataSource):
                log_info(
                    f"change local file format {source.file_format} to qianfan file"
                    f" format {self.inner_data_source_cache.format_type()}"
                )
                source.file_format = self.inner_data_source_cache.format_type()

            source.save(og_table, **kwargs)
            return og_table.inner_table

        # 如果是从本地转到其它源
        if isinstance(self.inner_data_source_cache, FileDataSource):
            source.save(self, **kwargs)
            return source.load(**kwargs)

        # 特判 Bos 到千帆
        if isinstance(self.inner_data_source_cache, BosDataSource) and isinstance(
            source, QianfanDataSource
        ):
            bos_helper = BosHelper(region=self.inner_data_source_cache.region)
            upload_data_from_bos_to_qianfan(
                bos_helper,
                self.inner_data_source_cache.bos_file_path.find(".zip") != -1,
                source.id,
                self.inner_data_source_cache.bucket,
                self.inner_data_source_cache.bos_file_path,
                **kwargs,
            )

            return None

        # 千帆到 Bos 暂不支持
        if isinstance(self.inner_data_source_cache, QianfanDataSource) and isinstance(
            source, BosDataSource
        ):
            err_msg = "can't save a qianfan dataset into bos"
            log_error(err_msg)
            raise ValueError(err_msg)

        # 其它情况可以尝试一下，然后捕捉报错
        try:
            source.save(self, **kwargs)
            return source.load(**kwargs)
        except Exception as e:
            err_msg = (
                f"saving dataset from {type(self.inner_data_source_cache)} to"
                f" {type(source)} has occurred an error: {e}"
            )
            log_error(err_msg)
            raise ValueError(err_msg)

    @classmethod
    def _from_args_to_source(
        cls,
        data_file: Optional[str] = None,
        qianfan_dataset_id: Optional[str] = None,
        qianfan_dataset_create_args: Optional[Dict[str, Any]] = None,
        bos_load_args: Optional[Dict[str, Any]] = None,
        bos_source_args: Optional[Dict[str, Any]] = None,
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
            return QianfanDataSource.create_bare_dataset(
                **qianfan_dataset_create_args, **kwargs
            )

        if bos_load_args:
            log_info(
                "construct a new qianfan data source from bos loading:"
                f" {bos_load_args}, with args: {kwargs}"
            )
            return QianfanDataSource.create_from_bos_file(**bos_load_args)

        if bos_source_args:
            return BosDataSource(**bos_source_args, **kwargs)

        log_info("no datasource was constructed")
        return None

    def _set_qianfan_default_io_column(self, source: DataSource) -> None:
        if not isinstance(source, QianfanDataSource):
            return

        template_type = source.template_type

        if template_type in [
            DataTemplateType.NonSortedConversation,
            DataTemplateType.SortedConversation,
            DataTemplateType.QuerySet,
        ]:
            self.input_columns = ["prompt"]

        if template_type in [
            DataTemplateType.NonSortedConversation,
            DataTemplateType.SortedConversation,
        ]:
            self.reference_column = "response"

    @classmethod
    def load(
        cls,
        source: Optional[DataSource] = None,
        data_file: Optional[str] = None,
        qianfan_dataset_id: Optional[str] = None,
        bos_load_args: Optional[Dict[str, Any]] = None,
        huggingface_dataset: Optional[Any] = None,
        bos_source_args: Optional[Dict[str, Any]] = None,
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
            qianfan_dataset_id (Optional[str]):
                qianfan dataset ID, default to None
            bos_load_args: (Optional[Dict[str, Any]]):
                create a dataset and import initial dataset content
                from args
            huggingface_dataset (Optional[Dict[str, Any], Any]):
                Huggingface dataset object, only support
                DatasetDict and Dataset of Huggingface datasets.
            bos_source_args: (Optional[Dict[str, Any]]):
                create arguments for creating a file on specific bos
                default to None
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
                bos_source_args=bos_source_args,
                **kwargs,
            )

        # 从数据源开始构建对象
        if not source:
            err_msg = "no data source or other arguments provided for loading"
            log_error(err_msg)
            raise ValueError(err_msg)

        table = cls._from_source(source, schema, **kwargs)

        if table.is_dataset_packed() and organize_data_as_group:
            table.unpack()

        # 校验
        if schema and table.inner_table and not schema.validate(table):
            error = ValidationError("validate failed when initialize dataset")
            log_error(str(error))
            raise error

        # 设置默认的数据列
        table._set_qianfan_default_io_column(source)

        return table

    def save(
        self,
        destination: Optional[DataSource] = None,
        data_file: Optional[str] = None,
        qianfan_dataset_id: Optional[str] = None,
        qianfan_dataset_create_args: Optional[Dict[str, Any]] = None,
        bos_source_args: Optional[Dict[str, Any]] = None,
        schema: Optional[Schema] = None,
        replace_source: Optional[bool] = None,
        **kwargs: Any,
    ) -> "Dataset":
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
            qianfan_dataset_id (Optional[str]):
                qianfan dataset ID, default to None
            qianfan_dataset_create_args: (Optional[Dict[str: Any]]):
                create arguments for creating a bare dataset on qianfan,
                default to None
            bos_source_args: (Optional[Dict[str, Any]]):
                create arguments for creating a file on specific bos
                default to None
            schema: (Optional[Schema]):
                schema used to validate before exporting data, default to None
            replace_source: (Optional[bool]):
                This parameter has been set as deprecated.
                if replace the original source, default to None
            kwargs (Any): optional arguments

        Returns:
            bool: is saving succeeded
        """
        if not destination:
            log_info("no destination data source was provided, construct")
            destination = self._from_args_to_source(
                data_file=data_file,
                qianfan_dataset_id=qianfan_dataset_id,
                qianfan_dataset_create_args=qianfan_dataset_create_args,
                bos_source_args=bos_source_args,
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
        table = self._to_source(source, **kwargs)  # noqa
        new_ds = Dataset(
            inner_table=table,
            inner_data_source_cache=source,
            inner_schema_cache=schema,
            input_columns=self.input_columns,
            reference_column=self.reference_column,
            eval_input_column=self.eval_input_column,
            eval_llm_output_column=self.eval_llm_output_column,
            **kwargs,
        )

        # 保持一致
        if new_ds.is_dataset_grouped():
            new_ds.pack()

        # 特判兼容原来的 replace_source 逻辑
        if replace_source is not None:
            log_warn('parameter "replace_source" has been set as deprecated')

        if not replace_source:
            return new_ds

        self.inner_table = new_ds.inner_table
        self.inner_data_source_cache = new_ds.inner_data_source_cache
        self.inner_schema_cache = new_ds.inner_schema_cache
        return self

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
            if isinstance(data[0], dict):
                return cls(
                    inner_table=pyarrow.Table.from_pylist(data).combine_chunks(),
                    inner_schema_cache=schema,
                    **kwargs,
                )
            elif isinstance(data[0], list):
                return cls(
                    inner_table=_construct_packed_table_from_nest_sequence(data),
                    inner_schema_cache=schema,
                    **kwargs,
                )
            elif isinstance(data[0], str):
                return cls(
                    inner_table=pyarrow.Table.from_pydict(
                        {QianfanDatasetPackColumnName: data}
                    ),
                    inner_schema_cache=schema,
                    **kwargs,
                )
            else:
                err_msg = f"unsupported element in list: {type(data[0])}"
                log_error(err_msg)
                raise ValueError(err_msg)
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
        return isinstance(self.inner_data_source_cache, QianfanDataSource)

    def _is_dataset_local(self) -> bool:
        return isinstance(self.inner_data_source_cache, FileDataSource)

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

    def start_online_data_process_task(self, operators: List[QianfanOperator]) -> str:
        """
        create an online ETL task on qianfan

        Args:
            operators (List[QianfanOperator]): operators applied to ETL task

        Returns:
            str: etl task id
        """

        if not self.is_dataset_located_in_qianfan():
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
            attr_dict = operator.dict()
            attr_dict.pop("operator_name")
            attr_dict.pop("operator_type")

            elem_dict = {"name": operator.operator_name, "args": attr_dict}

            operator_type = operator.operator_type
            operator_dict[operator_type].append(elem_dict)

        log_debug(f"operator args dict: {operator_dict}")
        log_info("start to creating an etl task")

        etl_id = _create_a_dataset_etl_task(
            self.inner_data_source_cache, operator_dict
        )[0]
        return etl_id

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
            result = _check_online_data_process_result(etl_id)
            if result is None:
                continue
            if not result:
                return ret_dict
            else:
                ret_dict["new_dataset_id"] = result
                ret_dict["is_succeeded"] = True
                break

        return ret_dict

    @_online_except_decorator
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
            {QianfanDataGroupColumnName: list(range(self.row_number()))}
        )

    @_online_except_decorator
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
    def map(self, op: Callable[[Any], Any], **kwargs: Any) -> Self:
        """
        map on dataset

        Args:
            op (Callable[[Any], Any]): handler used to map
            **kwargs (Any): other arguments

        Returns:
            Self: Dataset itself
        """
        assert isinstance(self.inner_data_source_cache, FileDataSource)
        return super().map(op, path=self.inner_data_source_cache.path, **kwargs)

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
        if self._is_dataset_local():
            log_info(f"list local dataset data by {by}")
            return super().list(by)
        elif self.is_dataset_located_in_qianfan():
            return _list_cloud_data(self.inner_data_source_cache, by, **kwargs)
        else:
            try:
                return super().list(by)
            except Exception:
                err_msg = (
                    "can't list dataset from data source:"
                    f" {type(self.inner_data_source_cache)}"
                )
                log_error(err_msg)
                raise ValueError(err_msg)

    def row_number(self) -> int:
        if self.is_dataset_located_in_qianfan():
            assert isinstance(self.inner_data_source_cache, QianfanDataSource)
            return Data.get_dataset_info(self.inner_data_source_cache.id)["result"][
                "versionInfo"
            ]["entityCount"]
        elif self._is_dataset_local():
            return super().row_number()
        else:
            try:
                return super().row_number()
            except Exception:
                err_msg = (
                    "can't get row number from data source:"
                    f" {type(self.inner_data_source_cache)}"
                )
                log_error(err_msg)
                raise ValueError(err_msg)

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
            elem (Dict[str, List]): a dict containing element added to dataset, which
                key as column name, value as column data
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

    @_online_except_decorator
    def column_number(self) -> int:
        """
        get dataset column count。

        Returns:
            int: column count。

        """
        return super().column_number()

    @_online_except_decorator
    def pack(self, **kwargs: Any) -> bool:
        """
        pack all group into 1 row
        and make table array-like with single column

        Args:
            **kwargs (Any): other arguments

        Returns:
            bool: whether packing succeeded
        """
        if isinstance(self.inner_data_source_cache, FileDataSource):
            return super().pack(path=self.inner_data_source_cache.path, **kwargs)
        else:
            return super().pack(**kwargs)

    @_online_except_decorator
    def unpack(self, **kwargs: Any) -> bool:
        """
        unpack all element in the row "_pack"
        make sure the element in the column "_pack"
        is Sequence[Dict[str, Any]]

        Args:
            **kwargs (Any): other arguments

        Returns:
            bool: whether unpacking succeeded
        """
        if isinstance(self.inner_data_source_cache, FileDataSource):
            return super().unpack(path=self.inner_data_source_cache.path, **kwargs)
        else:
            return super().unpack(**kwargs)

    @_online_except_decorator
    def to_pydict(self) -> Dict:
        """
        convert dataset to dict

        Returns:
            Dict: a dict
        """
        return super().to_pydict()

    @_online_except_decorator
    def to_pylist(self) -> List:
        """
        convert dataset to list

        Returns:
            List: a list
        """
        return super().to_pylist()

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
        model_version_id: Optional[str] = None,
        service_model: Optional[str] = None,
        service_endpoint: Optional[str] = None,
        is_chat_service: bool = True,
        does_show_latency: bool = True,
        output_prettified: bool = True,
        **kwargs: Any,
    ) -> "Dataset":
        """
        using arguments to init a llm instance
        and get output on current dataset from it
        set only model arguments our service arguments to instantiating

        Args:
            model_version_id (Optional[int]):
                version id of your own model, default to None
            service_model (Optional[str]):
                name of model you want to use as service, default to None
            service_endpoint (Optional[str]):
                endpoint of service, default to None
            is_chat_service (bool):
                the service type of service, default to True.
                Service will be Completion if False
            does_show_latency (bool):
                whether result dataset contain latency info column when
                using Service as evaluated object.
                Depending on different request mode (stream and non-stream),
                it will contains request_complete_latency or
                (first_token_latency, request_complete_latency) combo.
                Default to True
            output_prettified (bool):
                whether the result dataset should be prettified before return.
                Note: after set this arguments True, the function will
                return a Dataset which is saved on disk.
                Default to True, this default value makes function backward-compatible.
            **kwargs (Any):
                optional argument dict

        Returns:
            Dataset: A dataset contains inputs, reference outputs and llm outputs
        """

        if model_version_id:
            return self._batch_inference_on_model(
                model_version_id, output_prettified, **kwargs
            )
        elif service_model or service_endpoint:
            return self._batch_inference_on_service(
                service_model,
                service_endpoint,
                is_chat_service,
                does_show_latency,
                **kwargs,
            )
        else:
            err_msg = "no sufficient argument has been passed"
            log_error(err_msg)
            raise ValueError(err_msg)

    async def atest_using_llm(
        self,
        model_version_id: Optional[str] = None,
        service_model: Optional[str] = None,
        service_endpoint: Optional[str] = None,
        is_chat_service: bool = True,
        does_show_latency: bool = True,
        output_prettified: bool = True,
        **kwargs: Any,
    ) -> "Dataset":
        """
        using arguments to init a llm instance
        and get output on current dataset from it asynchronously
        set only model arguments our service arguments to instantiating

        Args:
            model_version_id (Optional[str]):
                version id of your own model, default to None
            service_model (Optional[str]):
                name of model you want to use as service, default to None
            service_endpoint (Optional[str]):
                endpoint of service, default to None
            is_chat_service (bool):
                the service type of service, default to True.
                Service will be Completion if False
            does_show_latency (bool):
                whether result dataset contain latency info column when
                using Service as evaluated object.
                Depending on different request mode (stream and non-stream),
                it will contains request_complete_latency or
                (first_token_latency, request_complete_latency) combo.
                Default to True
            output_prettified (bool):
                whether the result dataset should be prettified before return.
                Note: after set this arguments True, the function will
                return a Dataset which is saved on disk.
                Default to True, this default value makes function backward-compatible.
            **kwargs (Any):
                optional argument dict

        Returns:
            Dataset: A dataset contains inputs, reference outputs and llm outputs
        """

        if model_version_id:
            return self._batch_inference_on_model(
                model_version_id, output_prettified, **kwargs
            )
        elif service_model or service_endpoint:
            return await self._async_batch_inference_on_service(
                service_model,
                service_endpoint,
                is_chat_service,
                does_show_latency,
                **kwargs,
            )
        else:
            err_msg = "no sufficient argument has been passed"
            log_error(err_msg)
            raise ValueError(err_msg)

    def _batch_inference_on_model(
        self, model_version_id: str, output_prettified: bool, **kwargs: Any
    ) -> "Dataset":
        """
        create batch run using specific dataset on qianfan
        by evaluation ability of platform

        Parameters:
            model_version_id (str):
                version id of your own model, default to None
            output_prettified (bool):
                whether prettified output dataset content
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

        model_id = Model.detail(model_version_id)["result"]["modelIdStr"]

        result_dataset_id = _start_an_evaluation_task_for_model_batch_inference(
            self.inner_data_source_cache, model_id, model_version_id
        )

        result_dataset = Dataset.load(qianfan_dataset_id=result_dataset_id, **kwargs)
        if not output_prettified and result_dataset.is_dataset_located_in_qianfan():
            return result_dataset

        result_dataset.unpack()

        new_list: List[Dict[str, Any]] = []
        for entry in result_dataset.list():
            new_list.append(
                {
                    "prompt": entry["prompt"],
                    NewInputPromptColumnName: entry["prompt"],
                    LLMOutputColumnName: entry["model_response"][0]["content"],
                    OldReferenceColumnName: _extract_string(entry["response"]),
                }
            )

        return Dataset.create_from_pyobj(
            new_list,
            input_columns=["prompt"],
            reference_column=OldReferenceColumnName,
            eval_input_column=NewInputPromptColumnName,
            eval_llm_output_column=LLMOutputColumnName,
        )

    def _get_completion_return_dataset(
        self,
        input_str_list: List[str],
        output_list: List[str],
        request_latency_list: List[float],
        first_token_latency_list: List[float],
        does_show_latency: bool,
    ) -> "Dataset":
        table_dict = {
            **self.get_input_data,
            NewInputPromptColumnName: input_str_list,
            LLMOutputColumnName: output_list,
        }

        reference_column: Optional[str] = None
        if self.reference_column:
            table_dict[OldReferenceColumnName] = self.get_reference_data
            reference_column = OldReferenceColumnName

        if does_show_latency:
            if len(first_token_latency_list) != 0:
                table_dict[FirstTokenLatencyColumnName] = first_token_latency_list
            table_dict[RequestLatencyColumnName] = request_latency_list

        return Dataset.create_from_pyobj(
            table_dict,
            input_columns=self.input_columns,
            reference_column=reference_column,
            eval_input_column=NewInputPromptColumnName,
            eval_llm_output_column=LLMOutputColumnName,
        )

    def _get_chat_return_dataset(
        self,
        input_list: List[List[Dict[str, Any]]],
        output_list: List[str],
        reference_list: List[Any],
        request_latency_list: List[float],
        first_token_latency_list: List[float],
        does_show_latency: bool,
    ) -> "Dataset":
        if not self.is_dataset_grouped() and not self.is_dataset_packed():
            input_str_list = [conv[0]["content"] for conv in input_list]
            return self._get_completion_return_dataset(
                input_str_list,
                output_list,
                request_latency_list,
                first_token_latency_list,
                does_show_latency,
            )

        table_dict: Dict[str, Any] = {
            NewInputChatColumnName: input_list,
            LLMOutputColumnName: output_list,
            OldReferenceColumnName: reference_list,
        }

        if does_show_latency:
            if len(first_token_latency_list) != 0:
                table_dict[FirstTokenLatencyColumnName] = first_token_latency_list
            table_dict[RequestLatencyColumnName] = request_latency_list

        return Dataset.create_from_pyobj(
            table_dict,
            input_columns=[NewInputChatColumnName],
            reference_column=OldReferenceColumnName,
            eval_input_column=NewInputChatColumnName,
            eval_llm_output_column=LLMOutputColumnName,
        )

    def _batch_inference_on_service(
        self,
        service_model: Optional[str] = None,
        service_endpoint: Optional[str] = None,
        is_chat_service: bool = True,
        does_show_latency: bool = True,
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
            does_show_latency (bool):
                whether result dataset contain latency info column when
                using Service as evaluated object.
                Depending on different request mode (stream and non-stream),
                it will contains request_complete_latency or
                (first_token_latency, request_complete_latency) combo.
                Default to True
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

        service = _check_and_generate_service(
            self.input_columns,
            service_model,
            service_endpoint,
            is_chat_service,
            **kwargs,
        )

        if isinstance(service, Completion):
            input_str_list = self._get_input_str_list(**kwargs)
            output_list, request_latency_list, first_token_latency_list = (
                _batch_do_on_service(
                    service, input_str_list, system=system_prompt, **kwargs
                )
            )

            return self._get_completion_return_dataset(
                input_str_list,
                output_list,
                request_latency_list,
                first_token_latency_list,
                does_show_latency,
            )
        else:
            input_chat_list, reference_list = self._get_input_chat_list(**kwargs)
            output_list, request_latency_list, first_token_latency_list = (
                _batch_do_on_service(
                    service, input_chat_list, system=system_prompt, **kwargs
                )
            )

            return self._get_chat_return_dataset(
                input_chat_list,
                output_list,
                reference_list,
                request_latency_list,
                first_token_latency_list,
                does_show_latency,
            )

    async def _async_batch_inference_on_service(
        self,
        service_model: Optional[str] = None,
        service_endpoint: Optional[str] = None,
        is_chat_service: bool = True,
        does_show_latency: bool = True,
        system_prompt: str = "",
        **kwargs: Any,
    ) -> "Dataset":
        """
        asynchronously create batch run using specific dataset on qianfan

        Args:
            service_model (Optional[str]):
                name of model you want to use as service, default to None
            service_endpoint (Optional[str]):
                endpoint of service, default to None
            is_chat_service (bool):
                the service type of service, default to True.
                Service will be Completion if False
            does_show_latency (bool):
                whether result dataset contain latency info column when
                using Service as evaluated object.
                Depending on different request mode (stream and non-stream),
                it will contains request_complete_latency or
                (first_token_latency, request_complete_latency) combo.
                Default to True
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

        service = _check_and_generate_service(
            self.input_columns,
            service_model,
            service_endpoint,
            is_chat_service,
            **kwargs,
        )

        if isinstance(service, Completion):
            input_str_list = self._get_input_str_list(**kwargs)
            output_list, request_latency_list, first_token_latency_list = (
                await _async_batch_do_on_service(
                    service, input_str_list, system=system_prompt, **kwargs
                )
            )

            return self._get_completion_return_dataset(
                input_str_list,
                output_list,
                request_latency_list,
                first_token_latency_list,
                does_show_latency,
            )
        else:
            input_chat_list, reference_list = self._get_input_chat_list(**kwargs)
            output_list, request_latency_list, first_token_latency_list = (
                await _async_batch_do_on_service(
                    service, input_chat_list, system=system_prompt, **kwargs
                )
            )

            return self._get_chat_return_dataset(
                input_chat_list,
                output_list,
                reference_list,
                request_latency_list,
                first_token_latency_list,
                does_show_latency,
            )

    def _get_input_str_list(self, **kwargs: Any) -> List[str]:
        prompt_template: Optional[Prompt] = kwargs.get("prompt_template", None)
        input_dict = self.get_input_data
        assert self.input_columns

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
                            for column_name in self.input_columns
                        },
                        **kwargs,
                    )[0]
                )
            else:
                input_str_list.append(
                    "\n".join(
                        [
                            input_dict[column_name][i]
                            for column_name in self.input_columns
                        ]
                    )
                )

        return input_str_list

    def _get_input_chat_list(
        self, **kwargs: Any
    ) -> Tuple[List[List[Dict[str, Any]]], List[Any]]:
        if not self.is_dataset_packed() and not self.is_dataset_grouped():
            input_str_list = self._get_input_str_list(**kwargs)
            return [
                [{"role": QfRole.User.value, "content": prompt}]
                for prompt in input_str_list
            ], []

        assert self.input_columns

        if len(self.input_columns) > 1:
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

        input_column = self.input_columns[0]

        dataset = deepcopy(self)
        if dataset.is_dataset_grouped():
            dataset.pack()

        input_chat_list: List[List[Dict[str, Any]]] = []
        reference_list: List[Any] = []
        for chat in dataset.list():
            input_messages: List[Dict[str, Any]] = []
            for i in range(len(chat)):
                input_messages.append(
                    {"role": QfRole.User.value, "content": chat[i][input_column]}
                )
                reference = _extract_string(chat[i][reference_column])

                if i != len(chat) - 1:
                    input_messages.append(
                        {
                            "role": QfRole.Assistant.value,
                            "content": reference,
                        }
                    )
                else:
                    reference_list.append(reference)

            input_chat_list.append(input_messages)

        return input_chat_list, reference_list
