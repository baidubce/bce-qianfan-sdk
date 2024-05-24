import multiprocessing
import signal
import sys
from typing import List

import pandas as pd
import streamlit as st

table = sys.argv[1]


@st.cache_resource
def get_data():
    return table.list()


input_label: List[str] = []

with st.sidebar:
    for col_name in table.col_names():
        input_label.append(st.text_input(col_name + "过滤"))


pd_table = pd.DataFrame(get_data())

for label, column in zip(input_label, pd_table.columns):
    assert isinstance(label, str)

    if label == "":
        continue

    if label.isdigit():
        value = int(label)
        pd_table = pd_table[pd_table[column] == value]
    else:
        try:
            value = float(label)
            pd_table = pd_table[pd_table[column] == value]
        except:
            value = label
            pd_table = pd_table[pd_table[column].str.contains(value, na=False)]


def on_quit_button_clicked():
    signal.raise_signal(signal.SIGTERM)


with st.container:
    st.data_editor(pd_table, key="table")


button_quit = st.button("退出", on_click=on_quit_button_clicked)
