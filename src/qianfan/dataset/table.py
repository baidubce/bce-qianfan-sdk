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

    def map(self, op: Callable[[Any], Any]) -> Self:
        """
        map on pyarrow table's row

        Args:
            op (Callable[[Any], Any]): handler used to map

        Returns:
            Self: a new pyarrow table
        """

        # 构建出的新 table 会按照首行的 key 作为 columns
        if self._inner_table_is_packed():
            new_list: List[Union[List[Dict[str, Any]], str]] = []
            for row in self.table.column(QianfanDatasetPackColumnName).to_pylist():
                returned_data = op(row)
                if not returned_data:
                    log_warn("a row has been deleted from table")
                    continue
                if not isinstance(returned_data, (list, str)):
                    raise ValueError(
                        "returned value isn't list or str, rather"
                        f" {type(returned_data)}"
                    )

                new_list.append(returned_data)

            return pyarrow.Table.from_pydict({QianfanDatasetPackColumnName: new_list})
        else:
            new_table: List[Dict[str, Any]] = []
            is_grouped = self._inner_table_is_grouped()

            for row_index in range(self.table.num_rows):
                origin_data = self.table.take([row_index]).to_pylist()[0]
                input_dict = {key: val for key, val in origin_data.items()}
                group_number = (
                    None if not is_grouped else input_dict[QianfanDataGroupColumnName]
                )

                returned_data = op(input_dict)
                if not returned_data:
                    log_warn("a row has been deleted from table")
                    continue
                if not isinstance(returned_data, dict):
                    raise ValueError("returned value isn't dict")

                if is_grouped and QianfanDataGroupColumnName not in returned_data:
                    returned_data[QianfanDataGroupColumnName] = group_number

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
        if self._inner_table_is_packed():
            for row in self.table.column(QianfanDatasetPackColumnName).to_pylist():
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
        return _whether_dataset_is_packed(self.inner_table.column_names)

    def is_dataset_grouped(self) -> bool:
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

        self._squash_group_number()

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
