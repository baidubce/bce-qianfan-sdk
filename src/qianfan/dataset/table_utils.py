from typing import Any, Dict, List, Sequence

import pyarrow

from qianfan.dataset.consts import QianfanDataGroupColumnName


def _construct_table_from_nest_sequence(json_data_list: Sequence) -> pyarrow.Table:
    inner_list: List[Dict[str, Any]] = []
    for i in range(len(json_data_list)):
        for pair in json_data_list[i]:
            inner_list.append({**pair, QianfanDataGroupColumnName: i})
    return pyarrow.Table.from_pylist(inner_list)
