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

from qianfan.dataset.data_source import FileDataSource, FormatType, QianfanDataSource
from qianfan.resources.console.consts import (
    DataProjectType,
    DataSetType,
    DataStorageType,
    DataTemplateType,
)


def test_automatic_detect_file_format():
    assert FileDataSource(path="1.json").format_type() == FormatType.Json
    assert FileDataSource(path="1.2.jsonl").format_type() == FormatType.Jsonl
    assert FileDataSource(path="/1.csv").format_type() == FormatType.Csv
    assert FileDataSource(path="/2/1.txt").format_type() == FormatType.Text
    assert FileDataSource(path=".1.json").format_type() == FormatType.Json
    f = FileDataSource(path="123")
    f.set_format_type(FormatType.Json)
    assert f.format_type() == FormatType.Json


def test_create_bare_qianfan_data_source():
    datasource_1 = QianfanDataSource.create_new_bare_datasource_from_local(
        "name",
        DataTemplateType.NonSortedConversation,
        DataStorageType.PublicBos,
    )

    assert datasource_1.template_type == DataTemplateType.NonSortedConversation
    assert datasource_1.project_type == DataProjectType.Conversation
    assert datasource_1.set_type == DataSetType.TextOnly

    datasource_2 = QianfanDataSource.create_new_bare_datasource_from_local(
        "name",
        DataTemplateType.Text2Image,
        DataStorageType.PrivateBos,
        storage_args={
            "storage_id": "a",
            "storage_path": "b",
        },
    )

    assert datasource_2.template_type == DataTemplateType.Text2Image
    assert datasource_2.project_type == DataProjectType.Text2Image
    assert datasource_2.set_type == DataSetType.MultiModel
    assert (
        datasource_2.storage_path
        == "/easydata/_system_/dataset/ds-z07hkq2kyvsmrmdw/texts"
    )
    assert datasource_2.storage_id == "a"
    assert datasource_2.storage_region == "bj"
    assert datasource_2.format_type() == FormatType.Json


def test_create_qianfan_data_source_from_existed():
    source = QianfanDataSource.get_existed_datasource_from_qianfan(12, False)
    assert source.id == 12
    assert source.group_id == 14510
    assert source.storage_region == "bj"
