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
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple, Union

import pyarrow
import pyarrow.compute as pc
from pyarrow import Table as PyarrowTable
from pydantic import BaseModel
from typing_extensions import Self

from qianfan.dataset.consts import (
    QianfanDataGroupColumnName,
    QianfanDatasetPackColumnName,
)
from qianfan.dataset.process_interface import (
    Appendable,
    Listable,
    Processable,
)
from qianfan.dataset.utils import _construct_table_from_nest_sequence
from qianfan.utils import log_debug, log_error, log_info


class _PyarrowRowManipulator(BaseModel, Appendable, Listable, Processable):
    """handler for processing of pyarrow table row"""

    class Config:
        arbitrary_types_allowed = True

    table: PyarrowTable

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
        append an element to pyarrow table

        Args:
            elem (Union[List[Dict], Tuple[Dict], Dict]): elements added to pyarrow table
            is_dataset_packed (bool): whether table is packed, default to False.
            add_new_group (bool): whether elem has new group id, default to False.
            is_grouped (bool): whether elem is grouped, default to True.
            group_id (int): new group id, default to -1.
            **kwargs (Any): optional arguments
        Returns:
            Self: a new pyarrow table
        """

        if isinstance(elem, (list, tuple)):
            log_info("add a sequence object to table")
            if not elem:
                err_msg = "element is empty"
                log_error(err_msg)
                raise ValueError(err_msg)
            elif not isinstance(elem[0], dict):
                err_msg = (
                    "element in sequence-like "
                    "container cannot be instance of"
                    f" {type(elem[0])}"
                )
                log_error(err_msg)
                raise ValueError(err_msg)

            log_debug(f"append row data: {elem}")

            if is_dataset_packed:
                log_info("enter packed appending logic")
                table_dict = self.table.to_pydict()
                table_dict[QianfanDatasetPackColumnName].append(elem)
                return pyarrow.Table.from_pydict(table_dict)

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
            return pyarrow.concat_tables(
                [self.table, pyarrow.Table.from_pylist(tables)], promote=True
            )

        elif isinstance(elem, dict):
            log_info("add a dict object to table")
            if is_dataset_packed:
                elem = {QianfanDatasetPackColumnName: [elem]}
            elif group_id != -1:
                elem[QianfanDataGroupColumnName] = group_id + (
                    1 if add_new_group else 0
                )

            log_debug(f"row data after processing: {elem}")
            new_table = pyarrow.Table.from_pylist([elem])
            return pyarrow.concat_tables([self.table, new_table], promote=True)

        else:
            err_msg = f"element cannot be instance of {type(elem)}"
            log_error(err_msg)
            raise ValueError(err_msg)
        return self.table

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

    def map(self, op: Callable[[Any], Any]) -> Self:
        """
        map on pyarrow table's row

        Args:
            op (Callable[[Any], Any]): handler used to map

        Returns:
            Self: a new pyarrow table
        """

        # 构建出的新 table 会按照首行的 key 作为 columns
        new_table: List[Dict[str, Any]] = []
        for row_index in range(self.table.num_rows):
            origin_data = self.table.take([row_index]).to_pylist()[0]
            input_dict = {key: val for key, val in origin_data.items()}
            returned_data = op(input_dict)
            if not returned_data:
                raise ValueError("cant make data empty")
            if not isinstance(returned_data, dict):
                raise ValueError("returned value isn't dict")
            if input_dict.keys() != returned_data.keys():
                raise ValueError("cant modify column name in map")

            new_table.append(returned_data)

        return pyarrow.Table.from_pylist(new_table)

    def filter(self, op: Callable[[Any], bool]) -> Self:
        """
        filter on pyarrow table's row

        Args:
            op (Callable[[Any], bool]): handler used to filter

        Returns:
            Self: a new pyarrow table
        """

        selection_masks: List[bool] = []
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


class _PyarrowColumnManipulator(BaseModel, Appendable, Listable, Processable):
    """handler for processing of pyarrow table column"""

    class Config:
        arbitrary_types_allowed = True

    table: PyarrowTable

    def append(self, elem: Dict[str, List]) -> Self:
        """
        append a row to pyarrow table

        Args:
            elem (Dict[str, List]): dict containing element added to pyarrow table
                must has column name "name" and column data list "data"
        Returns:
            Self: a new pyarrow table
        """

        if not isinstance(elem, dict):
            raise ValueError(f"element appended must be dict, not {type(elem)}")
        if "name" not in elem:
            raise ValueError("no name has been provided")
        if "data" not in elem:
            raise ValueError("no data has been provided")
        if not isinstance(elem["name"], str):
            raise TypeError(f"name isn't str, rather than {type(elem['name'])}")
        if elem["name"] in self.table.column_names:
            raise ValueError(
                f"column name {elem['name']} has been in dataset column list"
            )
        if not isinstance(elem["data"], list):
            raise TypeError(f"data isn't list, rather than {type(elem['data'])}")
        if not elem["data"]:
            raise ValueError("data can't be empty")
        if len(elem["data"]) != self.table.num_rows:
            raise ValueError(
                f"the length of data need to be {self.table.num_rows}, rather than"
                f" {len(elem['data'])}"
            )
        return self.table.append_column(elem["name"], [elem["data"]])

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
            raise ValueError("contain not existed column name")
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


class Table(BaseModel, Appendable, Listable, Processable):
    """
    dataset representation on memory
    inherited from pyarrow.Table，implementing interface in process_interface.py
    """

    class Config:
        arbitrary_types_allowed = True

    inner_table: PyarrowTable

    def _row_op(self) -> _PyarrowRowManipulator:
        return _PyarrowRowManipulator(table=self.inner_table)

    def _col_op(self) -> _PyarrowColumnManipulator:
        return _PyarrowColumnManipulator(table=self.inner_table)

    def is_data_packed(self) -> bool:
        col_names = self.col_names()
        return len(col_names) == 1 and QianfanDatasetPackColumnName in col_names

    def is_data_grouped(self) -> bool:
        col_names = self.col_names()
        return QianfanDataGroupColumnName in col_names

    def pack(self) -> bool:
        """
        pack all group into 1 row
        and make table array-like with single column

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

        inner_index = "_index"
        group_ordered_table: pyarrow.Table = self.inner_table.append_column(
            inner_index, [list(range(self.row_number()))]
        ).sort_by(QianfanDataGroupColumnName)

        result_list: List[List[Dict[str, Any]]] = []
        for row in group_ordered_table.to_pylist():
            group_index = row[QianfanDataGroupColumnName]
            if group_index < 0:
                log_error(
                    f"row {row[inner_index]} has illegal group value:"
                    f" {row[QianfanDataGroupColumnName]}"
                )
                return False

            row.pop(inner_index)
            row.pop(QianfanDataGroupColumnName)

            while group_index >= len(result_list):
                result_list.append([])
            result_list[group_index].append(row)

        self.inner_table = pyarrow.Table.from_pydict(
            {QianfanDatasetPackColumnName: result_list}
        )
        return True

    def unpack(self) -> bool:
        """
        unpack all element in the row "_pack"
        make sure the element in the column "_pack"
        is Sequence[Dict[str, Any]]

        Returns:
            bool: whether unpacking succeeded
        """
        if QianfanDatasetPackColumnName not in self.col_names():
            log_error("can't pack a dataset without '_pack' column")
            return False

        if len(self.col_names()) != 1:
            log_error("dataset should only contain '_pack' column")
            return False

        if self.inner_table.column(QianfanDatasetPackColumnName).null_count:
            log_error("can't unpack a dataset when column '_pack' has None")
            return False

        element = self.list(0)[QianfanDatasetPackColumnName]
        if not (
            isinstance(element, (list, tuple))
            and element
            and isinstance(element[0], dict)
        ):
            log_error(f"dataset has element not supported: {element}")
            return False

        data_list = self.to_pydict()[QianfanDatasetPackColumnName]
        self.inner_table = _construct_table_from_nest_sequence(data_list)
        return True

    # 直接调用 Table 对象的接口方法都默认是在行上做处理
    def map(self, op: Callable[[Any], Any]) -> Self:
        """
        map on pyarrow table's row

        Args:
            op (Callable[[Any], Any]): handler used to map

        Returns:
            Self: Table itself
        """
        manipulator = self._row_op()
        self.inner_table = manipulator.map(op)  # noqa
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

        kwargs: Dict[str, Any] = {}
        if self.is_data_grouped():
            group_column: pyarrow.ChunkedArray = self.inner_table.column(
                QianfanDataGroupColumnName
            )
            group_id = pc.max(group_column, min_count=0).as_py()
            kwargs = {
                "group_id": group_id,
                "add_new_group": add_new_group,
                "is_grouped": is_grouped,
            }
        if self.is_data_packed():
            kwargs = {"is_dataset_packed": True}

        self.inner_table = manipulator.append(elem, **kwargs)
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
                must has column name "name" and column data list "data"
        Returns:
            Self: Table itself
        """
        manipulator = self._col_op()
        self.inner_table = manipulator.append(elem)
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
