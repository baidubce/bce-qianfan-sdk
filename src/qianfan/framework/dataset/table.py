from typing import Any, Callable, Dict, List, Optional, Sequence, Union

import pyarrow
from pyarrow import Table as PyarrowTable
from pydantic import BaseModel
from typing_extensions import Self

from qianfan.framework.dataset.process_interface import (
    Appendable,
    Listable,
    Processable,
)


class _PyarrowRowManipulator(BaseModel, Appendable, Listable, Processable):
    class Config:
        arbitrary_types_allowed = True

    table: PyarrowTable

    def append(self, elem: Any) -> Self:
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
        if isinstance(by, str) or (
            isinstance(by, (list, tuple)) and isinstance(by[0], str)
        ):
            raise ValueError("cannot get row from table by str")
        if not by:
            return self.table.to_pylist()

        if isinstance(by, int):
            return self.table.take([by]).to_pylist()
        elif isinstance(by, (list, tuple)):
            return self.table.take(by).to_pylist()
        elif isinstance(by, slice):
            return self.table.slice(
                offset=by.start, length=by.stop - by.start + 1
            ).to_pylist()
        else:
            raise ValueError(f"unsupported key type {type(by)} when get row from table")

    def map(self, op: Callable[[Any], Any]) -> Self:
        # 构建出的新 table 会按照首行的 key 作为 columns
        new_table: List[Dict[str, Any]] = []
        for row_index in range(self.table.num_rows):
            input_dict = {
                key: val[0]
                for key, val in self.table.take([row_index]).to_pydict().items()
            }
            new_table.append(op(input_dict))

        return pyarrow.Table.from_pylist(new_table)

    def filter(self, op: Callable[[Any], bool]) -> Self:
        selection_masks: List[bool] = []
        for row_index in range(self.table.num_rows):
            input_dict = {
                key: val[0]
                for key, val in self.table.take([row_index]).to_pydict().items()
            }
            selection_masks.append(op(input_dict))

        return self.table.filter(mask=selection_masks)

    def delete(self, index: Union[int, str]) -> Self:
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
    class Config:
        arbitrary_types_allowed = True

    table: PyarrowTable

    def append(self, elem: Any) -> Self:
        if not isinstance(elem, dict):
            raise ValueError(f"element appended must be dict, not {type(elem)}")
        return self.table.append_column(elem["name"], elem["data"])

    def list(
        self, by: Optional[Union[slice, int, str, Sequence[int], Sequence[str]]] = None
    ) -> Any:
        if not by:
            return self.table.to_pydict()

        if isinstance(by, slice):
            raise ValueError("cannot get column by slice")
        if isinstance(by, (int, str)):
            indices: Any = [by]
        else:
            indices = by
        return self.table.select(indices).to_pydict()

    def map(self, op: Callable[[Any], Any]) -> Self:
        new_columns: Dict[str, List[Any]] = {}
        for i in range(self.table.num_columns):
            column = self.table.select(i).to_pydict()
            new_columns += op(column)

        return pyarrow.Table.from_pydict(new_columns)

    def filter(self, op: Callable[[Any], bool]) -> Self:
        dropped_column_name = []
        for i in range(self.table.num_columns):
            column = self.table.select(i).to_pydict()
            if not op(column):
                dropped_column_name += list(column.keys())

        return self.table.drop_columns(dropped_column_name)

    def delete(self, index: Union[int, str]) -> Self:
        if isinstance(index, int):
            raise ValueError("cannot delete column by int")
        return self.table.drop_columns(index)


class Table(BaseModel, Appendable, Listable, Processable):
    """
    数据集在内存中的表示
    派生自 pyarrow.Table，并且实现了 process_interface.py 中的接口
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
        manipulator = self._row_op()
        self.inner_table = manipulator.map(op)  # noqa
        return self

    def filter(self, op: Callable[[Any], bool]) -> Self:
        manipulator = self._row_op()
        self.inner_table = manipulator.filter(op)
        return self

    def delete(self, index: Union[int, str]) -> Self:
        manipulator = self._row_op()
        self.inner_table = manipulator.delete(index)
        return self

    def append(self, elem: Any) -> Self:
        manipulator = self._row_op()
        self.inner_table = manipulator.append(elem)
        return self

    def list(
        self, by: Optional[Union[slice, int, str, Sequence[int], Sequence[str]]] = None
    ) -> Any:
        manipulator = self._row_op()
        return manipulator.list(by)

    def col_map(self, op: Callable[[Any], Any]) -> Self:
        manipulator = self._col_op()
        self.inner_table = manipulator.map(op)  # noqa
        return self

    def col_filter(self, op: Callable[[Any], bool]) -> Self:
        manipulator = self._col_op()
        self.inner_table = manipulator.filter(op)
        return self

    def col_delete(self, index: Union[int, str]) -> Self:
        manipulator = self._col_op()
        self.inner_table = manipulator.delete(index)
        return self

    def col_append(self, elem: Any) -> Self:
        manipulator = self._col_op()
        self.inner_table = manipulator.append(elem)
        return self

    def col_list(
        self, by: Optional[Union[slice, int, str, Sequence[int], Sequence[str]]] = None
    ) -> Any:
        manipulator = self._col_op()
        return manipulator.list(by)

    def col_names(self) -> List[str]:
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
