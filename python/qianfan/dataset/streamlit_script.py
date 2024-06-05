# Copyright (c) 2024 Baidu, Inc. All Rights Reserved.
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
"""data insight script for streamlit"""

import os
import re
import signal
import sys
from typing import Any, List, Optional, Tuple, Union

import pandas as pd
import streamlit as st

table = sys.argv[1]
insight_data = sys.argv[2]

metric_name_to_show_name = {
    "content_length": "文本字符数量",
    "special_characters_ratio": "特殊字符所占比例",
    "character_repetition_ratio": "字符重复比例",
}


@st.cache_resource
def get_data() -> Tuple[pd.DataFrame, Optional[pd.DataFrame], Optional[pd.DataFrame]]:
    pd_table = pd.DataFrame(table.list())  # type: ignore
    if insight_data is None:
        return pd_table, None, None

    metrics_dataframe_list = []
    assert isinstance(insight_data, dict)
    for column_name, metrics in insight_data.items():
        print(column_name)
        df = pd.DataFrame(metrics).rename(
            columns={
                metric_name: f"{column_name}_{metric_name}"
                for metric_name in metrics.keys()
            }
        )
        metrics_dataframe_list.append(df)

    metrics_dataframe_list.append(pd_table)
    overview_dataframe = pd.DataFrame(insight_data).applymap(lambda x: sum(x) / len(x))
    overview_dataframe.index = [
        metric_name_to_show_name[index] for index in overview_dataframe.index
    ]

    return (
        pd.concat(metrics_dataframe_list, axis=1),
        pd.DataFrame(insight_data).T,
        overview_dataframe,
    )


input_label: List[str] = []
pd_table, insight_table, mean_table = get_data()

with st.sidebar:
    for col_name in table.col_names():  # type: ignore
        input_label.append(
            st.text_input(col_name if col_name != "_pack" else "对话" + "过滤")
        )


for label, column in zip(input_label, table.col_names()):  # type: ignore
    assert isinstance(label, str)

    if label == "":
        continue

    if column == "_pack":

        def _pack_lambda_func(x: Any) -> bool:
            if isinstance(x, dict):
                for k, v in x.items():
                    return bool(re.search(label, k) or re.search(label, v))

            return False

        pd_table = pd_table[pd_table.applymap(_pack_lambda_func).any(axis=1)]
        continue

    value: Union[int, float, str]

    if label.isdigit():
        value = int(label)
        pd_table = pd_table[pd_table[column] == value]
    else:
        try:
            value = float(label)
            pd_table = pd_table[pd_table[column] == value]
        except Exception:
            value = label
            pd_table = pd_table[pd_table[column].str.contains(value, na=False)]


def on_quit_button_clicked() -> None:
    from multiprocessing import current_process

    os.kill(current_process().pid, signal.SIGTERM)  # type: ignore


if isinstance(mean_table, pd.DataFrame):
    st.text("均值统计表")
    st.data_editor(mean_table, use_container_width=True)

if isinstance(insight_table, pd.DataFrame):
    cols = st.columns(len(insight_table.columns))
    counter = 0

    for index, row in insight_table.items():
        cols[counter].text(metric_name_to_show_name[index])

        exploded_row = row.explode().to_frame()

        exploded_row["数值区间"] = pd.cut(
            exploded_row[index], 5, include_lowest=True
        ).astype(str)
        exploded_row["列名"] = exploded_row.index

        table_for_show = exploded_row.value_counts(["数值区间", "列名"]).reset_index(
            name="数量"
        )

        cols[counter].bar_chart(
            table_for_show,
            x="数值区间",
            y="数量",
            color="列名",
            use_container_width=True,
        )
        counter += 1

st.data_editor(pd_table, key="table", use_container_width=True)

button_quit = st.button("退出", on_click=on_quit_button_clicked)
