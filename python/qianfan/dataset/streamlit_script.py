import os
import signal
import sys
from typing import List, Optional, Tuple, Union

import pandas as pd
import streamlit as st

table = sys.argv[1]
insight_data = sys.argv[2]


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

    return (
        pd.concat(metrics_dataframe_list, axis=1),
        pd.DataFrame(insight_data).T,
        pd.DataFrame(insight_data).applymap(lambda x: sum(x) / len(x)),
    )


input_label: List[str] = []
pd_table, insight_table, mean_table = get_data()

with st.sidebar:
    for col_name in table.col_names():  # type: ignore
        input_label.append(st.text_input(col_name + "过滤"))


for label, column in zip(input_label, pd_table.columns):
    assert isinstance(label, str)

    if label == "":
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


col1, col2 = st.columns(2)

if isinstance(insight_table, pd.DataFrame):
    for index, row in insight_table.items():
        col1.text(index)

        exploded_row = row.explode().to_frame()

        exploded_row["grade"] = pd.cut(
            exploded_row[index], 5, include_lowest=True
        ).astype(str)
        exploded_row["column_name"] = exploded_row.index

        table_for_show = exploded_row.value_counts(
            ["grade", "column_name"]
        ).reset_index(name="count")

        col1.bar_chart(table_for_show, x="grade", y="count", color="column_name")

if isinstance(mean_table, pd.DataFrame):
    col2.data_editor(mean_table)

col2.data_editor(pd_table, key="table")


button_quit = st.button("退出", on_click=on_quit_button_clicked)
