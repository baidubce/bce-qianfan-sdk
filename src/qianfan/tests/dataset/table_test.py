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
test for data source
"""

from typing import Any, Dict

import pyarrow
import pytest

from qianfan.dataset.consts import (
    QianfanDataGroupColumnName,
    QianfanDatasetPackColumnName,
)
from qianfan.dataset.table import Table


def test_append_row():
    table = Table(
        inner_table=pyarrow.Table.from_pylist(
            [{"name": "duck", "age": 3}, {"name": "monkey", "age": 24}]
        )
    )

    with pytest.raises(ValueError):
        table.append(["not a dict"])

    with pytest.raises(ValueError):
        table.append(123)

    table = table.append({"name": "Alice", "age": 20})
    assert len(table.list()) == 3

    table = table.append([{"name": "Bob", "age": 22}, {"name": "Charlie", "age": 23}])
    assert len(table.list()) == 5


def test_list_row():
    table = Table(
        inner_table=pyarrow.Table.from_pydict({"a": [1, 2, 3], "b": ["a", "b", "c"]})
    )
    assert table.list(0) == {"a": 1, "b": "a"}
    assert table.list(1) == {"a": 2, "b": "b"}
    assert table.list([1, 2]) == [{"a": 2, "b": "b"}, {"a": 3, "b": "c"}]
    assert table.list((1, 2)) == [{"a": 2, "b": "b"}, {"a": 3, "b": "c"}]
    assert table.list(slice(1, 3)) == [{"a": 2, "b": "b"}, {"a": 3, "b": "c"}]
    with pytest.raises(Exception):
        table.list([1, 3])
    with pytest.raises(ValueError):
        table.list("a")
    with pytest.raises(ValueError):
        table.list(object())
    assert table.list() == [{"a": 1, "b": "a"}, {"a": 2, "b": "b"}, {"a": 3, "b": "c"}]


def test_map_row():
    table = Table(
        inner_table=pyarrow.Table.from_pydict({"a": [1, 2, 3], "b": ["a", "b", "c"]})
    )

    def plus1(obj: Dict) -> Dict:
        obj["a"] += 1
        return obj

    assert table.map(plus1).to_pydict() == {"a": [2, 3, 4], "b": ["a", "b", "c"]}

    # map操作的参数为空
    with pytest.raises(TypeError):
        table.map()

    # map操作的参数不为函数
    with pytest.raises(TypeError):
        table.map(1)

    # map操作的函数返回值为非字典
    with pytest.raises(ValueError):
        table.map(lambda x: 1)

    # map操作的函数返回值为空字典
    with pytest.raises(ValueError):
        table.map(lambda x: {})

    # map操作的函数返回值字典的键与首行不匹配
    with pytest.raises(ValueError):
        table.map(lambda x: {"c": x["a"]})


def test_filter_row():
    table = Table(inner_table=pyarrow.Table.from_pydict({"age": [1, 2, 3, 25, 26, 27]}))

    def op(row: Dict[str, Any]) -> bool:
        return row["age"] > 25

    filtered_table = table.filter(op)
    assert filtered_table.row_number() == 2

    def mis_op(row):
        return row["age"]

    with pytest.raises(ValueError):
        table.filter(mis_op)

    def return_none_op(row):
        return None

    with pytest.raises(ValueError):
        table.filter(return_none_op)


def test_delete_row():
    table = Table(inner_table=pyarrow.Table.from_pydict({"x": [1, 2, 3, 4]}))

    assert table.delete(0).to_pydict() == {"x": [2, 3, 4]}
    assert table.delete(1).to_pydict() == {"x": [2, 4]}
    assert table.delete(1).to_pydict() == {"x": [2]}

    with pytest.raises(ValueError):
        table.delete("string")

    with pytest.raises(OverflowError):
        table.delete(5)

    with pytest.raises(OverflowError):
        table.delete(-1)


def test_append_column():
    table = Table(inner_table=pyarrow.Table.from_pydict({"x": [1, 2, 3, 4]}))
    with pytest.raises(ValueError):
        table.col_append(123)

    with pytest.raises(ValueError):
        table.col_append({"name": "test"})

    with pytest.raises(ValueError):
        table.col_append({"data": "abc"})

    with pytest.raises(TypeError):
        table.col_append({"name": 1, "data": "abc"})

    with pytest.raises(TypeError):
        table.col_append({"name": "test", "data": "abc"})
    with pytest.raises(ValueError):
        table.col_append({"name": "test", "data": ["abc"]})

    table.col_append({"name": "test", "data": ["a", "b", "c", "d"]})

    with pytest.raises(ValueError):
        table.col_append({"name": "test", "data": ["a", "b", None, "d"]})


def test_list_column():
    table = Table(
        inner_table=pyarrow.Table.from_pydict(
            {"x": [1, 2, 3, 4], "y": ["a", "b", "c", "c"]}
        )
    )

    assert table.col_list() == {"x": [1, 2, 3, 4], "y": ["a", "b", "c", "c"]}
    assert table.col_list(0) == {"x": [1, 2, 3, 4]}
    assert table.col_list("y") == {"y": ["a", "b", "c", "c"]}

    with pytest.raises(ValueError):
        table.col_list("z")

    assert table.col_list(("x", "y")) == {"x": [1, 2, 3, 4], "y": ["a", "b", "c", "c"]}
    assert table.col_list(["x", "y"]) == {"x": [1, 2, 3, 4], "y": ["a", "b", "c", "c"]}

    # Test with slice
    with pytest.raises(ValueError):
        table.col_list(slice(0, 5))


def test_map_column():
    table = Table(
        inner_table=pyarrow.Table.from_pydict(
            {"x": [1, 2, 3, 4], "y": ["a", "b", "c", "c"], "z": ["1", "2", "3", "4"]}
        )
    )

    def op(column: Any) -> Any:
        for k, v in column.items():
            if k == "x":
                return {"new_x": v}
            if k == "y":
                return {"new_y": [1, 2, 3, 4]}
            return {k: v}

    assert table.col_map(op).to_pydict() == {
        "new_x": [1, 2, 3, 4],
        "new_y": [1, 2, 3, 4],
        "z": ["1", "2", "3", "4"],
    }


def test_filter_column():
    table = Table(
        inner_table=pyarrow.Table.from_pydict(
            {"x": [1, 2, 3, 4], "y": ["a", "b", "c", "c"], "z": ["1", "2", "3", "4"]}
        )
    )

    def op(column: Any) -> bool:
        for k, v in column.items():
            return k == "x"

    assert set(table.col_filter(op).to_pydict().keys()) == {"x"}


def test_delete_column():
    table = Table(
        inner_table=pyarrow.Table.from_pydict(
            {"x": [1, 2, 3, 4], "y": ["a", "b", "c", "c"], "z": ["1", "2", "3", "4"]}
        )
    )

    assert table.col_delete("y").to_pydict() == {
        "x": [1, 2, 3, 4],
        "z": ["1", "2", "3", "4"],
    }


def test_unpack_table():
    packed_table = {
        QianfanDatasetPackColumnName: [
            [
                {"column1": "data1", "column2": "data2"},
                {"column1": "data1", "column2": "data2"},
            ],
            [{"column1": "data1", "column2": "data2"}],
        ]
    }

    table = Table(inner_table=pyarrow.Table.from_pydict(packed_table))

    assert table.unpack()
    unpacked_inner_table = [
        {"column1": "data1", "column2": "data2", QianfanDataGroupColumnName: 0},
        {"column1": "data1", "column2": "data2", QianfanDataGroupColumnName: 0},
        {"column1": "data1", "column2": "data2", QianfanDataGroupColumnName: 1},
    ]
    assert table.list() == unpacked_inner_table


def test_pack_table():
    unpacked_inner_table = [
        {"column1": "data1", "column2": "data2", QianfanDataGroupColumnName: 0},
        {"column1": "data1", "column2": "data2", QianfanDataGroupColumnName: 0},
        {"column1": "data1", "column2": "data2", QianfanDataGroupColumnName: 1},
    ]

    table = Table(inner_table=pyarrow.Table.from_pylist(unpacked_inner_table))

    assert table.pack()
    packed_table = {
        QianfanDatasetPackColumnName: [
            [
                {"column1": "data1", "column2": "data2"},
                {"column1": "data1", "column2": "data2"},
            ],
            [{"column1": "data1", "column2": "data2"}],
        ]
    }

    packed_row_table = [
        {
            QianfanDatasetPackColumnName: [
                {"column1": "data1", "column2": "data2"},
                {"column1": "data1", "column2": "data2"},
            ]
        },
        {QianfanDatasetPackColumnName: [{"column1": "data1", "column2": "data2"}]},
    ]

    assert table.col_list() == packed_table
    assert table.list() == packed_row_table


def test_packed_dataset_append():
    packed_table = {
        QianfanDatasetPackColumnName: [
            [
                {"column1": "data1", "column2": "data2"},
                {"column1": "data1", "column2": "data2"},
            ],
            [{"column1": "data1", "column2": "data2"}],
        ]
    }

    table = Table(inner_table=pyarrow.Table.from_pydict(packed_table))

    table.append(elem={"column1": "data1", "column2": "data2"})
    assert table.row_number() == 3

    table.append(
        elem=[
            {"column1": "data1", "column2": "data2"},
            {"column1": "data1", "column2": "data2"},
        ]
    )
    assert table.row_number() == 4

    new_table_element = {
        QianfanDatasetPackColumnName: [
            [
                {"column1": "data1", "column2": "data2"},
                {"column1": "data1", "column2": "data2"},
            ],
            [{"column1": "data1", "column2": "data2"}],
            [{"column1": "data1", "column2": "data2"}],
            [
                {"column1": "data1", "column2": "data2"},
                {"column1": "data1", "column2": "data2"},
            ],
        ]
    }

    assert table.col_list() == new_table_element


def test_grouped_dataset_append():
    unpacked_inner_table = [
        {"column1": "data1", "column2": "data2", QianfanDataGroupColumnName: 0},
        {"column1": "data1", "column2": "data2", QianfanDataGroupColumnName: 0},
        {"column1": "data1", "column2": "data2", QianfanDataGroupColumnName: 1},
    ]

    table = Table(inner_table=pyarrow.Table.from_pylist(unpacked_inner_table))

    table.append(elem={"column1": "data1", "column2": "data2"})
    assert table.list()[-1][QianfanDataGroupColumnName] == 1

    table.append(elem={"column1": "data1", "column2": "data2"}, add_new_group=True)
    assert table.list()[-1][QianfanDataGroupColumnName] == 2

    table.append(elem={"column1": "data1", "column2": "data2"})
    assert table.list()[-1][QianfanDataGroupColumnName] == 2

    table.append(
        elem=[
            {"column1": "data1", "column2": "data2"},
            {"column1": "data1", "column2": "data2"},
        ]
    )
    assert table.list()[-1][QianfanDataGroupColumnName] == 2
    assert table.list()[-2][QianfanDataGroupColumnName] == 2

    table.append(
        elem=[
            {"column1": "data1", "column2": "data2"},
            {"column1": "data1", "column2": "data2"},
        ],
        add_new_group=True,
    )
    assert table.list()[-1][QianfanDataGroupColumnName] == 3
    assert table.list()[-2][QianfanDataGroupColumnName] == 3

    table.append(
        elem=[
            {"column1": "data1", "column2": "data2"},
            {"column1": "data1", "column2": "data2"},
        ],
        add_new_group=True,
        is_grouped=False,
    )
    assert table.list()[-1][QianfanDataGroupColumnName] == 5
    assert table.list()[-2][QianfanDataGroupColumnName] == 4
