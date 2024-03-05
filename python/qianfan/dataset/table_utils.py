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
utilities table needs
"""
from typing import Any, Dict, List, Sequence

import pyarrow

from qianfan.dataset.consts import (
    QianfanDataGroupColumnName,
    QianfanDatasetPackColumnName,
)


def _construct_table_from_nest_sequence(
    json_data_list: Sequence, group_index: int, **kwargs: Any
) -> List[Dict[str, Any]]:
    inner_list: List[Dict[str, Any]] = []
    for pair in json_data_list:
        inner_list.append({**pair, QianfanDataGroupColumnName: group_index})
    return inner_list


def _construct_packed_table_from_nest_sequence(
    json_data_list: Sequence, **kwargs: Any
) -> pyarrow.Table:
    return pyarrow.Table.from_pydict({QianfanDatasetPackColumnName: json_data_list})
