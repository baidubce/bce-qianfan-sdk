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
import os
import shutil

from qianfan.dataset.data_source import FileDataSource, FormatType, QianfanDataSource
from qianfan.resources.console.consts import (
    DataProjectType,
    DataSetType,
    DataStorageType,
    DataTemplateType,
)


def test_automatic_detect_file_format():
    with open("1.json", "w"):
        ...
    with open("1.2.jsonl", "w"):
        ...
    with open("1.csv", "w"):
        ...
    with open("1.txt", "w"):
        ...
    with open(".1.json", "w"):
        ...
    with open("123", "w"):
        ...

    assert FileDataSource(path="1.json").format_type() == FormatType.Json
    assert FileDataSource(path="1.2.jsonl").format_type() == FormatType.Jsonl
    assert FileDataSource(path="1.csv").format_type() == FormatType.Csv
    assert FileDataSource(path="1.txt").format_type() == FormatType.Text
    assert FileDataSource(path=".1.json").format_type() == FormatType.Json
    f = FileDataSource(path="123")
    f.set_format_type(FormatType.Json)
    assert f.format_type() == FormatType.Json

    os.remove("1.json")
    os.remove("1.2.jsonl")
    os.remove("1.csv")
    os.remove("1.txt")
    os.remove(".1.json")
    os.remove("123")


def test_read_from_folder():
    os.makedirs("test_dirs", exist_ok=True)
    with open("test_dirs/test_file1.txt", "w") as f:
        f.write("test_file1")

    with open("test_dirs/test_file2.txt", "w") as f:
        f.write("test_file2")

    f = FileDataSource(path="test_dirs")
    content = f.fetch()
    content_list = content.split(os.linesep)
    content_list.sort()

    assert content_list == ["test_file1", "test_file2"]

    shutil.rmtree("test_dirs")


def test_create_bare_qianfan_data_source():
    datasource_1 = QianfanDataSource.create_bare_dataset(
        "name",
        DataTemplateType.NonSortedConversation,
        DataStorageType.PublicBos,
    )

    assert datasource_1.template_type == DataTemplateType.NonSortedConversation
    assert datasource_1.project_type == DataProjectType.Conversation
    assert datasource_1.set_type == DataSetType.TextOnly

    datasource_2 = QianfanDataSource.create_bare_dataset(
        "name",
        DataTemplateType.Text2Image,
        DataStorageType.PrivateBos,
        storage_id="a",
        storage_path="b",
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
    source = QianfanDataSource.get_existed_dataset(12, False)
    assert source.id == 12
    assert source.group_id == 14510
    assert source.storage_region == "bj"
