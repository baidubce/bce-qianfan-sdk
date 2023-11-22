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
test for data set
"""

from typing import Any

import pytest
from pydantic import BaseModel

from qianfan.dataset.consts import QianfanDefaultColumnNameForNestedTable
from qianfan.dataset.data_source import DataSource, FormatType
from qianfan.dataset.dataset import Dataset
from qianfan.dataset.schema import (
    QianfanNonSortedConversation,
    QianfanSortedConversation,
)


class FakeDataSource(DataSource, BaseModel):
    buffer: str = ""
    origin_data: str
    format: FormatType

    def save(self, data: str, **kwargs: Any) -> bool:
        self.buffer = data
        return True

    async def asave(self, data: str, **kwargs: Any) -> bool:
        pass

    def fetch(self, **kwargs: Any) -> str:
        return self.origin_data  # noqa

    async def afetch(self, **kwargs: Any) -> str:
        pass

    def format_type(self) -> FormatType:
        return self.format

    def set_format_type(self, format_type: FormatType) -> None:
        self.format = format_type


def test_dataset_create():
    fake_data_source = FakeDataSource(
        origin_data=(
            '[{"prompt": "12", "response": [["12"]]}, {"prompt": "12", "response":'
            ' [["12"]]}]'
        ),
        format=FormatType.Jsonl,
    )
    dataset = Dataset.load(fake_data_source)
    list_ret = dataset.list()
    dataset.save(schema=QianfanNonSortedConversation())
    dataset.save(schema=QianfanSortedConversation())
    assert fake_data_source.buffer == fake_data_source.fetch()
    assert list(list_ret[0].keys())[0] == QianfanDefaultColumnNameForNestedTable

    fake_data_source_2 = FakeDataSource(
        origin_data='{"prompt": "12", "response": [["12"]]}', format=FormatType.Json
    )
    dataset_2 = Dataset.load(fake_data_source_2)
    list_ret = dataset_2.list()
    dataset_2.save(schema=QianfanNonSortedConversation())
    dataset_2.save(schema=QianfanSortedConversation())
    assert f"[{fake_data_source_2.fetch()}]" == fake_data_source_2.buffer
    assert list(list_ret[0].keys())[0] == "prompt"

    fake_data_source_3 = FakeDataSource(
        origin_data='{"prompt": "12", "response": [[]]}', format=FormatType.Json
    )
    dataset_3 = Dataset.load(fake_data_source_3)
    with pytest.raises(Exception):
        dataset_3.save(schema=QianfanNonSortedConversation())
    with pytest.raises(Exception):
        dataset_3.save(schema=QianfanSortedConversation())

    fake_data_source_4 = FakeDataSource(
        origin_data='[{"prompt": "12", "response": [["12"]]}, {"prompt": "12"}]',
        format=FormatType.Jsonl,
    )
    dataset_4 = Dataset.load(fake_data_source_4)
    with pytest.raises(Exception):
        dataset_4.save(schema=QianfanNonSortedConversation())
    with pytest.raises(Exception):
        dataset_4.save(schema=QianfanSortedConversation())
