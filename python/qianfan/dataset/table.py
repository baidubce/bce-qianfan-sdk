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
wrapper for pyarrow.Table
"""
import threading
from typing import (
    Any,
    Callable,
    Dict,
    Generator,
    List,
    Optional,
    Sequence,
    Tuple,
    Union,
)

import pyarrow
import pyarrow.compute as pc
from pyarrow import Table as PyarrowTable
from typing_extensions import Self

from qianfan.dataset.consts import (
    QianfanDataGroupColumnName,
    QianfanDatasetPackColumnName,
)
from qianfan.dataset.process_interface import (
    Addable,
    Listable,
    Processable,
)
from qianfan.dataset.table_utils import _construct_table_from_nest_sequence
from qianfan.utils import log_debug, log_error, log_info, log_warn
from qianfan.utils.pydantic import BaseModel


def _create_new_table_for_add(
    elem: Union[
        List[List[Dict]], List[Dict], Tuple[Dict], Dict, List[str], Tuple[str], str
    ],
    is_dataset_packed: bool = False,
    add_new_group: bool = False,
    is_grouped: bool = True,
    group_id: int = -1,
    **kwargs: Any,
) -> PyarrowTable:
    if isinstance(elem, (list, tuple)):
        log_info("add a sequence object to table")
        if not elem:
            err_msg = "element is empty"
            log_error(err_msg)
            raise ValueError(err_msg)

        log_debug(f"append row data: {elem}")

        if is_dataset_packed:
            log_info("enter packed appending logic")
            if isinstance(elem[0], dict):
                return pyarrow.Table.from_pydict({QianfanDatasetPackColumnName: [elem]})
            elif isinstance(elem[0], list) and isinstance(elem[0][0], dict):
                return pyarrow.Table.from_pydict({QianfanDatasetPackColumnName: elem})
            elif isinstance(elem[0], str):
                return pyarrow.Table.from_pydict({QianfanDatasetPackColumnName: elem})
            else:
                err_msg = f"element cannot be instance of {type(elem)}"
                log_error(err_msg)
                raise ValueError(err_msg)

        if not isinstance(elem[0], dict):
            err_msg = (
                "element in sequence-like "
                "container cannot be instance of"
                f" {type(elem[0])}"
            )
            log_error(err_msg)
            raise ValueError(err_msg)

        # TODO 是否需要做深拷贝？
        tables: List = list(elem)

        if group_id != -1:
            log_info("enter grouped appending logic")

            if not add_new_group:
                for table in tables:
                    table[QianfanDataGroupColumnName] = group_id
            elif is_grouped:
                for table in tables:
                    table[QianfanDataGroupColumnName] = group_id + 1
            else:
                for i in range(len(tables)):
                    table = tables[i]
                    table[QianfanDataGroupColumnName] = group_id + i + 1

            log_debug(f"row data after processing: {table}")
        return pyarrow.Table.from_pylist(tables)

    elif isinstance(elem, dict):
        log_info("add a dict object to table")
        if is_dataset_packed:
            elem = {QianfanDatasetPackColumnName: [elem]}
        elif group_id != -1:
            elem[QianfanDataGroupColumnName] = group_id + (1 if add_new_group else 0)

        log_debug(f"row data after processing: {elem}")
        return pyarrow.Table.from_pylist([elem])
    elif isinstance(elem, str):
        if not is_dataset_packed:
            err_msg = "can't add string when your table isn't packed"
            log_error(err_msg)
            raise ValueError(err_msg)
        return pyarrow.Table.from_pylist([{QianfanDatasetPackColumnName: elem}])
    else:
        err_msg = f"element cannot be instance of {type(elem)}"
        log_error(err_msg)
        raise ValueError(err_msg)


def _whether_dataset_is_packed(col_names: List[str]) -> bool:
    return col_names == [QianfanDatasetPackColumnName]


def _whether_dataset_is_grouped(col_names: List[str]) -> bool:
    return QianfanDataGroupColumnName in col_names


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


class _PyarrowRowManipulator(BaseModel, Addable, Listable, Processable):
    """handler for processing of pyarrow table row"""

    class Config:
        arbitrary_types_allowed = True

    table: PyarrowTable

    def _inner_table_is_packed(self) -> bool:
        return _whether_dataset_is_packed(self.table.column_names)

    def _inner_table_is_grouped(self) -> bool:
        return _whether_dataset_is_grouped(self.table.column_names)

    def append(
        self,
        elem: Union[List[Dict], Tuple[Dict], Dict],
        is_dataset_packed: bool = False,
        add_new_group: bool = False,
        is_grouped: bool = True,
        group_id: int = -1,
        **kwargs: Any,
    ) -> Self:
        """
        append element(s) to pyarrow table

        Args:
            elem (Union[List[Dict], Tuple[Dict], Dict]):
                element(s) added to pyarrow table
            is_dataset_packed (bool): whether table is packed, default to False.
            add_new_group (bool): whether elem has new group id, default to False.
            is_grouped (bool): whether elem is grouped, default to True.
            group_id (int): new group id, default to -1.
            **kwargs (Any): optional arguments
        Returns:
            Self: a new pyarrow table
        """

        return pyarrow.concat_tables(
            [
                self.table,
                _create_new_table_for_add(
                    elem,
                    is_dataset_packed,
                    add_new_group,
                    is_grouped,
                    group_id,
                    **kwargs,
                ),
            ],
            promote=True,
        )

    def insert(
        self,
        elem: Union[List[Dict], Tuple[Dict], Dict],
        index: int,
        is_dataset_packed: bool = False,
        add_new_group: bool = False,
        is_grouped: bool = True,
        group_id: int = -1,
        **kwargs: Any,
    ) -> Self:
        """
        insert element(s) to pyarrow table

        Args:
            elem (Union[List[Dict], Tuple[Dict], Dict]):
                element(s) added to pyarrow table
            index (int): where to insert element(s).
            is_dataset_packed (bool): whether table is packed, default to False.
            add_new_group (bool): whether elem has new group id, default to False.
            is_grouped (bool): whether elem is grouped, default to True.
            group_id (int): new group id, default to -1.
            **kwargs (Any): optional arguments
        Returns:
            Self: a new pyarrow table
        """
        table_length = self.table.num_rows
        if index < 0 or index > table_length:
            err_msg = f"can't insert element at {index}"
            log_error(err_msg)
            raise ValueError(err_msg)

        if index == table_length:
            return self.append(
                elem, is_dataset_packed, add_new_group, is_grouped, group_id, **kwargs
            )

        new_table = _create_new_table_for_add(
            elem, is_dataset_packed, add_new_group, is_grouped, group_id, **kwargs
        )

        if index == 0:
            return pyarrow.concat_tables([new_table, self.table], promote=True)

        table_front_part = self.table.slice(length=index)
        table_rear_part = self.table.slice(index)
        return pyarrow.concat_tables(
            [table_front_part, new_table, table_rear_part], promote=True
        )

    def list(
        self, by: Optional[Union[slice, int, str, Sequence[int], Sequence[str]]] = None
    ) -> Any:
        """
        get element(s) from pyarrow table

        Args:
            by (Optional[Union[slice, int, Sequence[int]]]):
                index or indices for elements, default to None, in which case
                return a python list of pyarrow table row
        Returns:
            Any: pyarrow table row list
        """

        if isinstance(by, str) or (
            isinstance(by, (list, tuple)) and isinstance(by[0], str)
        ):
            raise ValueError("cannot get row from table by str")

        if self._inner_table_is_packed():
            if by is None:
                return self.table.to_pydict()[QianfanDatasetPackColumnName]
            if isinstance(by, int):
                return self.table.take([by]).to_pylist()[0][
                    QianfanDatasetPackColumnName
                ]
            elif isinstance(by, (list, tuple)):
                return self.table.take(list(by)).to_pydict()[
                    QianfanDatasetPackColumnName
                ]
            elif isinstance(by, slice):
                return self.table.slice(
                    offset=by.start, length=by.stop - by.start + 1
                ).to_pydict()[QianfanDatasetPackColumnName]
            else:
                raise ValueError(
                    f"unsupported key type {type(by)} when get row from table"
                )

        if by is None:
            return self.table.to_pylist()
        if isinstance(by, int):
            return self.table.take([by]).to_pylist()[0]
        elif isinstance(by, (list, tuple)):
            return self.table.take(list(by)).to_pylist()
        elif isinstance(by, slice):
            return self.table.slice(
                offset=by.start, length=by.stop - by.start + 1
            ).to_pylist()
        else:
            raise ValueError(f"unsupported key type {type(by)} when get row from table")

    def map(
        self,
        op: Callable[[Any], Any],
        batch_size: int = 10000,
        path: str = "./default_path",
        keep_original_order: bool = True,
        **kwargs: Any,
    ) -> Self:
        """
        map on pyarrow table's row

        Args:
            op (Callable[[Any], Any]): handler used to map
            batch_size (int): batch size of concurrent processing
            path (str): where to save temporary arrow file
            keep_original_order (bool): does table after mapping will keep
                same order with OG Table, default to True
            **kwargs (Any): other arguments

        Returns:
            Self: a new pyarrow table
        """

        # 构建出的新 table 会按照首行的 key 作为 columns
        # 现在处理都是按照单行为单位处理，
        # 这样子做的目的是确保每次处理时只会有一条数据被读入到内存中，
        # 防止一次性读入全部数据，丧失 Memory-Map 的含义
        # 后续需要优化成 Batch + 多线程的形式来优化数据集处理速度

        # 如果数据集是被 pack 起来的，则按照一行作为一个列表，传递给 op 函数

        # 创建一个任务分配器，来分配需要处理的区间
        task_dispatcher = TaskDispatcher(batch_size, self.table.num_rows)

        if self._inner_table_is_packed():

            def _mapper_closure(
                batch_index: int, batch_size: int
            ) -> Generator[Any, None, None]:
                # 拿到一个区间任务并取出区间数据
                rows = self.table.slice(batch_index, batch_size).to_pydict()[
                    QianfanDatasetPackColumnName
                ]

                # 开始处理并且放在结果集合里面
                for row in rows:
                    returned_data = op(row)
                    if not returned_data:
                        log_warn("a row has been deleted from table")
                        continue
                    if not isinstance(returned_data, (list, str)):
                        raise ValueError(
                            "returned value isn't list or str, rather"
                            f" {type(returned_data)}"
                        )

                    yield returned_data

        else:
            is_grouped = self._inner_table_is_grouped()

            def _mapper_closure(
                batch_index: int, batch_size: int
            ) -> Generator[Any, None, None]:
                rows = self.table.slice(batch_index, batch_size).to_pylist()
                for row in rows:
                    input_dict = {key: val for key, val in row.items()}
                    group_number = (
                        None
                        if not is_grouped
                        else input_dict[QianfanDataGroupColumnName]
                    )
                    returned_data = op(input_dict)

                    if not returned_data:
                        log_warn("a row has been deleted from table")
                        continue
                    if not isinstance(returned_data, dict):
                        raise ValueError("returned value isn't dict")

                    if is_grouped and QianfanDataGroupColumnName not in returned_data:
                        returned_data[QianfanDataGroupColumnName] = group_number

                    yield returned_data

        from qianfan.dataset.data_source.utils import _create_map_arrow_file

        return _create_map_arrow_file(
            path=path,
            **kwargs,
            mapper_closure=task_dispatcher.mapper_closure(_mapper_closure),
            keep_original_order=keep_original_order,
        )

    def filter(self, op: Callable[[Any], bool]) -> Self:
        """
        filter on pyarrow table's row

        Args:
            op (Callable[[Any], bool]): handler used to filter

        Returns:
            Self: a new pyarrow table
        """

        selection_masks: List[bool] = []
        if self._inner_table_is_packed():
            for row_index in range(self.table.num_rows):
                row = self.table.take([row_index]).to_pylist()[0][
                    QianfanDatasetPackColumnName
                ]
                flag = op(row)
                if flag is None:
                    raise ValueError("cant return None")
                if not isinstance(flag, bool):
                    raise ValueError("returned value isn't bool")

                selection_masks.append(flag)
        else:
            for row_index in range(self.table.num_rows):
                origin_data = self.table.take([row_index]).to_pylist()[0]
                input_dict = {key: val for key, val in origin_data.items()}
                flag = op(input_dict)
                if flag is None:
                    raise ValueError("cant return None")
                if not isinstance(flag, bool):
                    raise ValueError("returned value isn't bool")

                selection_masks.append(flag)

        return self.table.filter(mask=selection_masks)

    def delete(self, index: Union[int, str]) -> Self:
        """
        delete an element from pyarrow table

        Args:
            index (Union[int, str]): element index to delete

        Returns:
            Self: a new pyarrow table
        """

        if isinstance(index, str):
            raise ValueError("cannot delete row by str")
        table_length = self.table.num_rows
        if index < 0 or index >= table_length:
            raise OverflowError(f"index overflow, table length is {table_length}")
        if index == 0:
            return self.table.slice(1)
        elif index == table_length - 1:
            return self.table.slice(0, table_length - 1)
        return pyarrow.concat_tables(
            [self.table.slice(0, index), self.table.slice(index + 1)]
        )


class _PyarrowColumnManipulator(BaseModel, Addable, Listable, Processable):
    """handler for processing of pyarrow table column"""

    class Config:
        arbitrary_types_allowed = True

    table: PyarrowTable

    def append(self, elem: Dict[str, List]) -> Self:
        """
        append a row to pyarrow table

        Args:
            elem (Dict[str, List]): dict containing element added to pyarrow table
                key as column name, value as column data
        Returns:
            Self: a new pyarrow table
        """

        if not isinstance(elem, dict):
            raise ValueError(f"element appended must be dict, not {type(elem)}")

        for name, data in elem.items():
            if name in self.table.column_names:
                raise ValueError(f"column name {name} has been in dataset column list")

            if not isinstance(data, list):
                raise TypeError(f"data isn't list, rather than {type(data)}")

            if len(data) != self.table.num_rows:
                raise ValueError(
                    f"the length of data need to be {self.table.num_rows}, rather than"
                    f" {len(data)}"
                )

            self.table = self.table.append_column(name, [data])

        return self.table

    def insert(self, elem: Dict[str, List], index: int) -> Self:
        """
        insert a row to pyarrow table

        Args:
            elem (Dict[str, List]): dict containing element added to pyarrow table
                must has column name "name" and column data list "data"
            index (int): where to insert new column

        Returns:
            Self: a new pyarrow table
        """

        col_length = self.table.num_columns
        if index < 0 or index > col_length:
            err_msg = f"can't insert column at {index}"
            log_error(err_msg)
            raise ValueError(err_msg)

        if index == col_length:
            return self.append(elem)

        return self.table.add_column(index, elem["name"], [elem["data"]])

    def list(
        self, by: Optional[Union[slice, int, str, Sequence[int], Sequence[str]]] = None
    ) -> Any:
        """
        get column(s) from pyarrow table

        Args:
            by (Optional[Union[int, str, Sequence[int], Sequence[str]]]):
                index or indices for columns, default to None, in which case
                return a python list of pyarrow table column
        Returns:
            Any: pyarrow table column list
        """

        if by is None:
            return self.table.to_pydict()

        if isinstance(by, slice):
            raise ValueError("cannot get column by slice")
        if isinstance(by, (int, str)):
            indices: Any = [by]
        else:
            indices = by
        if isinstance(indices[0], str) and not set(indices).issubset(
            set(self.table.column_names)
        ):
            raise ValueError(f"contain not existed column name: {indices}")
        return self.table.select(list(indices)).to_pydict()

    def map(self, op: Callable[[Any], Any]) -> Self:
        """
        map on pyarrow table's column

        Args:
            op (Callable[[Any], Any]): handler used to map

        Returns:
            Self: a new pyarrow table
        """

        new_columns: Dict[str, List[Any]] = {}
        for i in range(self.table.num_columns):
            column = self.table.select([i]).to_pydict()
            ret_column = op(column)
            new_columns.update(ret_column)

        return pyarrow.Table.from_pydict(new_columns)

    def filter(self, op: Callable[[Any], bool]) -> Self:
        """
        filter on pyarrow table's column

        Args:
            op (Callable[[Any], bool]): handler used to filter

        Returns:
            Self: a new pyarrow table
        """

        dropped_column_name = []
        for i in range(self.table.num_columns):
            column = self.table.select([i]).to_pydict()
            if not op(column):
                dropped_column_name += list(column.keys())

        return self.table.drop_columns(dropped_column_name)

    def delete(self, index: Union[int, str]) -> Self:
        """
        delete an column from pyarrow table

        Args:
            index (str): column name to delete

        Returns:
            Self: a new pyarrow table
        """

        if isinstance(index, int):
            raise ValueError("cannot delete column by int")
        return self.table.drop_columns(index)

    def col_renames(self, new_names: List[str]) -> Self:
        """
        rename all dataset column

        Args:
            new_names (List[str]): All new names for columns
        Returns:
            Self: a new pyarrow table
        """

        if (
            _whether_dataset_is_grouped(self.table.column_names)
            and QianfanDataGroupColumnName not in new_names
        ):
            i = self.table.column_names.index(QianfanDataGroupColumnName)
            new_names.insert(i, QianfanDataGroupColumnName)

        return self.table.rename_columns(new_names)


class Table(Addable, Listable, Processable):
    """
    dataset representation on memory
    inherited from pyarrow.Table，implementing interface in process_interface.py
    """

    def __init__(self, inner_table: PyarrowTable) -> None:
        """
        Init a Table object

        Args:
            inner_table (PyarrowTable): a pyarrow.Table object wrapped by Table
        """
        # 内部使用的 pyarrow.Table 对象
        self.inner_table: PyarrowTable = inner_table

    def _row_op(self) -> _PyarrowRowManipulator:
        return _PyarrowRowManipulator(table=self.inner_table)

    def _col_op(self) -> _PyarrowColumnManipulator:
        return _PyarrowColumnManipulator(table=self.inner_table)

    def is_dataset_packed(self) -> bool:
        if not self.inner_table:
            return False
        return _whether_dataset_is_packed(self.inner_table.column_names)

    def is_dataset_grouped(self) -> bool:
        if not self.inner_table:
            return False
        return _whether_dataset_is_grouped(self.inner_table.column_names)

    def _squash_group_number(self) -> None:
        if not self.is_dataset_grouped():
            log_warn("squash group number when table isn't grouped")
            return

        self.inner_table = self.inner_table.sort_by(QianfanDataGroupColumnName)
        group_column_list = self.col_list(QianfanDataGroupColumnName)[
            QianfanDataGroupColumnName
        ]

        last_appeared_number = group_column_list[0]
        current_group_number = 0
        new_group_column_list = [0]

        for i in range(1, len(group_column_list)):
            num = group_column_list[i]
            if num != last_appeared_number:
                last_appeared_number = num
                current_group_number += 1

            new_group_column_list.append(current_group_number)

        self.col_delete(QianfanDataGroupColumnName)
        self.col_append({QianfanDataGroupColumnName: new_group_column_list})

        return

    def pack(
        self, batch_size: int = 10000, path: str = "./default_path", **kwargs: Any
    ) -> bool:
        """
        pack all group into 1 row
        and make table array-like with single column

        Args:
            batch_size (int): batch size of concurrent processing
            path (str): where to save temporary arrow file
            **kwargs (Any): other arguments

        Returns:
            bool: whether packing succeeded
        """
        if QianfanDataGroupColumnName not in self.col_names():
            log_error("can't pack a dataset without '_group' column")
            return False

        if len(self.col_names()) == 1:
            log_error("can't pack a dataset only with '_group' column")
            return False

        if self.inner_table.column(QianfanDataGroupColumnName).null_count:
            log_error("can't pack a dataset when column '_group' has None")
            return False

        self._squash_group_number()

        # 添加用于定位错误的 _index 列，并且按照压缩后的组号重排数据
        inner_index = "_index"
        group_ordered_table: pyarrow.Table = self.inner_table.append_column(
            inner_index, [list(range(self.row_number()))]
        ).sort_by(QianfanDataGroupColumnName)

        # 用于合并由于切分数据集而导致被分割的同组元素的一个 Dict
        # 键是由下一个切片的开始索引
        merge_dict: Dict[int, Tuple[int, List[Dict[str, Any]]]] = {}

        task_dispatcher = TaskDispatcher(batch_size, self.inner_table.num_rows)

        def _pack_closure(
            batch_index: int, batch_size: int
        ) -> Generator[Any, None, None]:
            # 当前组别的数据缓存
            group_data: List[Dict[str, Any]] = []

            rows = group_ordered_table.slice(batch_index, batch_size).to_pylist()
            # 记录当前处理的组号
            current_group_index: int = rows[0][QianfanDataGroupColumnName]

            # 记录是否需要合并组
            is_first_group_chunk: bool = True

            for i in range(len(rows)):
                group_index = rows[i][QianfanDataGroupColumnName]
                if group_index < 0:
                    err_msg = (
                        f"row {rows[i][inner_index]} has illegal group value:"
                        f" {rows[i][QianfanDataGroupColumnName]}"
                    )
                    log_error(err_msg)
                    raise ValueError(err_msg)

                rows[i].pop(inner_index)
                rows[i].pop(QianfanDataGroupColumnName)

                # 当读完所有当前组的数据后，返回一次
                if group_index != current_group_index:
                    if is_first_group_chunk:
                        is_first_group_chunk = False
                        if batch_index in merge_dict:
                            data_tuple = merge_dict[batch_index]
                            if data_tuple[0] == group_index:
                                group_data += data_tuple[1]
                            del merge_dict[batch_index]

                    current_group_index = group_index
                    yield group_data
                    group_data = []

                group_data.append(rows[i])

            # 结束后再把剩下没有返回的给丢到合并字典中
            if group_data:
                if batch_index + batch_size < self.inner_table.num_rows:
                    merge_dict[batch_index + batch_size] = (
                        current_group_index,
                        group_data,
                    )
                else:
                    # 如果是最后一组，则不合并，抛出
                    yield group_data

        from qianfan.dataset.data_source.utils import _create_map_arrow_file

        self.inner_table = _create_map_arrow_file(
            path=path,
            **kwargs,
            mapper_closure=task_dispatcher.mapper_closure(_pack_closure),
        )
        return True

    def unpack(
        self, batch_size: int = 10000, path: str = "./default_path", **kwargs: Any
    ) -> bool:
        """
        unpack all element in the row "_pack"
        make sure the element in the column "_pack"
        is Sequence[Dict[str, Any]]

        Args:
            batch_size (int): batch size of concurrent processing
            path (str): where to save temporary arrow file
            **kwargs (Any): other arguments

        Returns:
            bool: whether unpacking succeeded
        """
        if QianfanDatasetPackColumnName not in self.col_names():
            log_warn("can't pack a dataset without '_pack' column")
            return False

        if len(self.col_names()) != 1:
            log_warn("dataset should only contain '_pack' column")
            return False

        if self.inner_table.column(QianfanDatasetPackColumnName).null_count:
            log_warn("can't unpack a dataset when column '_pack' has None")
            return False

        element = self.list(0)
        if not (
            isinstance(element, (list, tuple))
            and element
            and isinstance(element[0], dict)
        ):
            log_warn(f"dataset has element not supported: {element}")
            return False

        task_dispatcher = TaskDispatcher(batch_size, self.inner_table.num_rows)

        def _unpack_closure(
            batch_index: int, batch_size: int
        ) -> Generator[Any, None, None]:
            rows = self.inner_table.slice(batch_index, batch_size).to_pydict()[
                QianfanDatasetPackColumnName
            ]
            for i in range(len(rows)):
                returned_data = _construct_table_from_nest_sequence(
                    rows[i], batch_index + i
                )

                for data in returned_data:
                    yield data

        from qianfan.dataset.data_source.utils import _create_map_arrow_file

        self.inner_table = _create_map_arrow_file(
            path=path,
            **kwargs,
            mapper_closure=task_dispatcher.mapper_closure(_unpack_closure),
        )
        return True

    # 直接调用 Table 对象的接口方法都默认是在行上做处理
    def map(self, op: Callable[[Any], Any], **kwargs: Any) -> Self:
        """
        map on pyarrow table's row

        Args:
            op (Callable[[Any], Any]): handler used to map
            **kwargs (Any): other arguments

        Returns:
            Self: Table itself
        """
        manipulator = self._row_op()
        if not callable(op):
            err_msg = "op has type {type}, rather than callable"
            log_error(err_msg)
            raise TypeError(err_msg)

        self.inner_table = manipulator.map(op, **kwargs)  # noqa
        return self

    def filter(self, op: Callable[[Any], bool]) -> Self:
        """
        filter on pyarrow table's row

        Args:
            op (Callable[[Any], bool]): handler used to filter

        Returns:
            Self: Table itself
        """
        manipulator = self._row_op()
        self.inner_table = manipulator.filter(op)
        return self

    def delete(self, index: Union[int, str]) -> Self:
        """
        delete an element from pyarrow table

        Args:
            index (Union[int, str]): element index to delete

        Returns:
            Self: Table itself
        """
        manipulator = self._row_op()
        self.inner_table = manipulator.delete(index)
        return self

    def _calculate_kwargs_for_add(
        self, add_new_group: bool = False, is_grouped: bool = True, group_id: int = -1
    ) -> Dict[str, Any]:
        kwargs: Dict[str, Any] = {}
        if self.is_dataset_grouped():
            if group_id != -1:
                kwargs = {
                    "group_id": group_id - 1,
                    "add_new_group": True,
                    "is_grouped": is_grouped,
                }
                return kwargs

            group_column: pyarrow.ChunkedArray = self.inner_table.column(
                QianfanDataGroupColumnName
            )
            calculated_group_id = pc.max(group_column, min_count=0).as_py()
            kwargs = {
                "group_id": calculated_group_id,
                "add_new_group": add_new_group,
                "is_grouped": is_grouped,
            }
        elif self.is_dataset_packed():
            kwargs = {"is_dataset_packed": True}

        return kwargs

    def append(
        self, elem: Any, add_new_group: bool = False, is_grouped: bool = True
    ) -> Self:
        """
        append an element to pyarrow table

        Args:
            elem (Union[List[Dict], Tuple[Dict], Dict]): Elements added to pyarrow table
            add_new_group (bool):
                Whether elem has a new group id.
                Only used when table is grouped.
            is_grouped (bool):
                Are element in elem in same group.
                Only used when table is grouped and elem is Sequence
                and add_new_group was set True.
                Default to True, all elements
                will be in same group.
                If it's True, each element will have
                sequential incremental group id from last
                available group id.
        Returns:
            Self: Table itself
        """
        manipulator = self._row_op()

        self.inner_table = manipulator.append(
            elem, **self._calculate_kwargs_for_add(add_new_group, is_grouped)
        )
        return self

    def insert(
        self,
        elem: Any,
        index: Any,
        group_id: int = -1,
        add_new_group: bool = False,
        is_grouped: bool = True,
    ) -> Self:
        """
        insert an element to pyarrow table

        Args:
            elem (Union[List[Dict], Tuple[Dict], Dict]): Elements added to pyarrow table
            index (int): where to insert element(s)
            group_id (int):
                which group id you want to apply to new element(s).
                Default to -1, which means let group id be automatically
                inferred from table.
            add_new_group (bool):
                Whether elem has a new group id.
                Only used when table is grouped
                and group_id is -1
            is_grouped (bool):
                Are element in elem in same group.
                Only used when table is grouped and elem is Sequence
                and add_new_group was set True.
                Default to True, all elements
                will be in same group.
                If it's True, each element will have
                sequential incremental group id from last
                available group id.
        Returns:
            Self: Table itself
        """
        manipulator = self._row_op()

        self.inner_table = manipulator.insert(
            elem,
            index,
            **self._calculate_kwargs_for_add(add_new_group, is_grouped, group_id),
        )
        return self

    def list(
        self, by: Optional[Union[slice, int, str, Sequence[int], Sequence[str]]] = None
    ) -> Any:
        """
        get element(s) from pyarrow table

        Args:
            by (Optional[Union[slice, int, Sequence[int]]]):
                index or indices for elements, default to None, in which case
                return a python list of pyarrow table row
        Returns:
            Any: pyarrow table row list
        """
        manipulator = self._row_op()
        return manipulator.list(by)

    def col_map(self, op: Callable[[Any], Any]) -> Self:
        """
        map on pyarrow table's column

        Args:
            op (Callable[[Any], Any]): handler used to map

        Returns:
            Self: Table itself
        """
        manipulator = self._col_op()
        self.inner_table = manipulator.map(op)  # noqa
        return self

    def col_filter(self, op: Callable[[Any], bool]) -> Self:
        """
        filter on pyarrow table's column

        Args:
            op (Callable[[Any], bool]): handler used to filter

        Returns:
            Self: Table itself
        """
        manipulator = self._col_op()
        self.inner_table = manipulator.filter(op)
        return self

    def col_delete(self, index: Union[int, str]) -> Self:
        """
        delete a column from pyarrow table

        Args:
            index (str): column name to delete

        Returns:
            Self: Table itself
        """
        manipulator = self._col_op()
        self.inner_table = manipulator.delete(index)
        return self

    def col_append(self, elem: Any) -> Self:
        """
        append a row to pyarrow table

        Args:
            elem (Dict[str, List]): dict containing element added to pyarrow table
                key as column name, value as column data
        Returns:
            Self: Table itself
        """
        manipulator = self._col_op()
        self.inner_table = manipulator.append(elem)
        return self

    def col_insert(self, elem: Any, index: Any) -> Self:
        """
        append a row to pyarrow table

        Args:
            elem (Dict[str, List]): dict containing element added to pyarrow table
                must has column name "name" and column data list "data"
            index (int): where to insert new column
        Returns:
            Self: Table itself
        """
        manipulator = self._col_op()
        self.inner_table = manipulator.insert(elem, index)
        return self

    def col_list(
        self, by: Optional[Union[slice, int, str, Sequence[int], Sequence[str]]] = None
    ) -> Any:
        """
        get column(s) from pyarrow table

        Args:
            by (Optional[Union[int, str, Sequence[int], Sequence[str]]]):
                index or indices for columns, default to None, in which case
                return a python list of pyarrow table column
        Returns:
            Any: pyarrow table column list
        """
        manipulator = self._col_op()
        return manipulator.list(by)

    def col_names(self) -> List[str]:
        """
        get column name list

        Returns:
            List[str]: column name list
        """
        return self.inner_table.column_names

    def col_renames(self, new_names: List[str]) -> Self:
        """
        rename all dataset column

        Args:
            new_names (List[str]): All new names for columns
        Returns:
            Self: A brand-new Table with new name
        """
        manipulator = self._col_op()
        self.inner_table = manipulator.col_renames(new_names)
        return self

    # 重写 get 和 del 的魔法方法
    def __getitem__(self, key: Any) -> Any:
        if isinstance(key, str) or (
            isinstance(key, Sequence) and isinstance(key[0], str)
        ):
            return self.col_list(key)
        return self.list(key)

    def __delitem__(self, key: Any) -> None:
        if isinstance(key, str):
            self.col_delete(key)
        elif isinstance(key, int):
            self.delete(key)
        else:
            raise ValueError(f"Unsupported key type {type(key)}")

    def __len__(self) -> int:
        return self.row_number()

    def row_number(self) -> int:
        """
        get pyarrow table row count。

        Returns:
            int: row count。

        """
        return self.inner_table.num_rows

    def column_number(self) -> int:
        """
        get pyarrow table column count。

        Returns:
            int: column count。

        """
        return self.inner_table.num_columns

    def to_pylist(self) -> List:
        """
        convert a pyarrow table to list

        Returns:
            List: a list
        """
        return self.inner_table.to_pylist()

    def to_pydict(self) -> Dict:
        """
        convert a pyarrow table to dict

        Returns:
            Dict: a dict
        """
        return self.inner_table.to_pydict()
