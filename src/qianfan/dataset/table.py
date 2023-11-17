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
from pyarrow import Table as PyarrowTable
from pydantic import BaseModel
from typing_extensions import Self

from qianfan.dataset.process_interface import (
    Appendable,
    Listable,
    Processable,
)


class _PyarrowRowManipulator(BaseModel, Appendable, Listable, Processable):
    """handler for processing of pyarrow table row"""

    class Config:
        arbitrary_types_allowed = True

    table: PyarrowTable

    def append(self, elem: Union[List[Dict], Tuple[Dict], Dict]) -> Self:
        """
        append an element to pyarrow table

        Args:
            elem (Union[List[Dict], Tuple[Dict], Dict]): elements added to pyarrow table
        Returns:
            Self: a new pyarrow table
        """

        if isinstance(elem, (list, tuple)):
            if not elem:
                raise ValueError("element is empty")
            elif not isinstance(elem[0], dict):
                raise ValueError(
                    "element in sequence-like container cannot be instance of"
                    f" {type(elem[0])}"
                )
            else:
                tables = []
                for e in elem:
                    tables.append(
                        pyarrow.Table.from_pydict(
                            mapping={k: [v] for k, v in e.items()}
                        )
                    )
                return pyarrow.concat_tables([self.table, *tables], promote=True)
        elif isinstance(elem, dict):
            new_table = pyarrow.Table.from_pydict(
                mapping={k: [v] for k, v in elem.items()}
            )
            return pyarrow.concat_tables([self.table, new_table], promote=True)
        else:
            raise ValueError(f"element cannot be instance of {type(elem)}")
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
            return self.table.take([by]).to_pylist()
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

    def append(self, elem: Any) -> Self:
        """
        append an element to pyarrow table

        Args:
            elem (Union[List[Dict], Tuple[Dict], Dict]): elements added to pyarrow table
        Returns:
            Self: Table itself
        """
        manipulator = self._row_op()
        self.inner_table = manipulator.append(elem)
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
        delete an column from pyarrow table

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

    def get_row_count(self) -> int:
        """
        get pyarrow table row count。

        Returns:
            int: row count。

        """
        return self.inner_table.num_rows

    def get_column_count(self) -> int:
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
