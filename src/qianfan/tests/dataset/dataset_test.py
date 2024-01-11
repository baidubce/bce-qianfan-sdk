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
from unittest.mock import patch

import pytest

from qianfan.dataset.consts import QianfanDataGroupColumnName
from qianfan.dataset.data_operator import FilterCheckNumberWords
from qianfan.dataset.data_source import DataSource, FormatType, QianfanDataSource
from qianfan.dataset.dataset import Dataset
from qianfan.dataset.schema import (
    QianfanGenericText,
    QianfanNonSortedConversation,
    QianfanSortedConversation,
)
from qianfan.pydantic import BaseModel
from qianfan.resources.console.consts import DataTemplateType


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
    dataset = Dataset.load(fake_data_source, organize_data_as_group=False)
    list_ret = dataset.list()
    dataset.save(schema=QianfanNonSortedConversation())
    dataset.save(schema=QianfanSortedConversation())
    assert fake_data_source.buffer == fake_data_source.fetch()
    assert "prompt" in list_ret[0][0].keys()

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

    fake_data_source_5 = FakeDataSource(
        origin_data=(
            '[{"prompt": "12", "response": [["12"]]}, {"prompt": "12", "response":'
            ' [["12"]]}]\n'
            '[{"prompt": "12", "response": [["12"]]}, {"prompt": "12"}]'
        ),
        format=FormatType.Jsonl,
    )
    dataset_5 = Dataset.load(fake_data_source_5)
    with pytest.raises(Exception):
        dataset_5.save(schema=QianfanNonSortedConversation())
    with pytest.raises(Exception):
        dataset_5.save(schema=QianfanSortedConversation())

    fake_data_source_6 = FakeDataSource(
        origin_data="this\nis\nmulti\nline\ndata", format=FormatType.Text
    )
    dataset_6 = Dataset.load(fake_data_source_6)
    dataset_6.save(schema=QianfanGenericText())

    assert fake_data_source_6.origin_data == fake_data_source_6.buffer


def test_dataset_online_process():
    qianfan_data_source = QianfanDataSource.create_bare_dataset(
        "test", DataTemplateType.GenericText
    )
    dataset = Dataset.load(source=qianfan_data_source)
    assert dataset.online_data_process(
        [FilterCheckNumberWords(number_words_min_cutoff=10)]
    )["is_succeeded"]


def test_manipulator_group_add_and_delete():
    dataset = Dataset.create_from_pyobj(
        [{"test_column": "456"}, {"test_column": "123"}]
    )
    dataset.add_default_group_column()

    assert QianfanDataGroupColumnName in dataset.col_names()
    assert dataset.list()[1][QianfanDataGroupColumnName] == 1

    dataset.delete_group_column()

    assert QianfanDataGroupColumnName not in dataset.col_names()


def test_branch_load():
    fds = FakeDataSource(origin_data="", format=FormatType.Jsonl)
    with pytest.raises(ValueError, match="no data in jsonline file"):
        Dataset.load(source=fds)

    fds.origin_data = '{"prompt": "result"}'
    ds = Dataset.load(source=fds)
    fds.format = FormatType.Csv
    ds.save(fds)
    fds.origin_data = fds.buffer
    Dataset.load(fds)


@patch("qianfan.dataset.data_source.upload_content_to_bos", return_value=None)
@patch("qianfan.dataset.data_source.upload_file_to_bos", return_value=None)
def test_branch_save(*args, **kwargs):
    fake_data_source = FakeDataSource(
        origin_data=(
            '[{"prompt": "12", "response": [["12"]]}, {"prompt": "12", "response":'
            ' [["12"]]}]'
        ),
        format=FormatType.Jsonl,
    )
    ds = Dataset.load(source=fake_data_source)
    ds.unpack()
    ds.save(fake_data_source)

    from qianfan.tests.dataset.data_source_test import (
        create_an_empty_qianfan_datasource,
    )

    fake_qianfan_data_source = create_an_empty_qianfan_datasource()
    ds = Dataset.create_from_pyobj([{"prompt": "nihao", "response": [["hello"]]}])

    ds.save(fake_qianfan_data_source)
    ds.save(FakeDataSource(origin_data="", format=FormatType.Jsonl))

    fake_qianfan_data_source = create_an_empty_qianfan_datasource()
    fake_qianfan_data_source.data_format_type = FormatType.Text
    fake_qianfan_data_source.template_type = DataTemplateType.GenericText
    fake_qianfan_data_source.project_type = DataTemplateType.GenericText
    ds = Dataset.create_from_pyobj({"text": ["wenben"]})
    ds.save(fake_qianfan_data_source)

    ds = Dataset.create_from_pyobj({"prompt": [1, 2], "response": [3, 4]})
    ds.save(FakeDataSource(origin_data="", format=FormatType.Csv))
    with pytest.raises(ValueError):
        ds.save(FakeDataSource(origin_data="", format=FormatType.Text))
