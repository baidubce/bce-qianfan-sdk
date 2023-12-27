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
import json
import os
import shutil
from unittest.mock import patch

import pytest
from pytest_mock import MockerFixture

from qianfan import get_config
from qianfan.dataset.consts import QianfanDatasetLocalCacheDir
from qianfan.dataset.data_source import FileDataSource, FormatType, QianfanDataSource
from qianfan.resources.console.consts import (
    DataProjectType,
    DataSetType,
    DataStorageType,
    DataTemplateType,
)


def test_automatic_detect_file_format():
    try:
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
        with pytest.raises(ValueError, match="file path not found"):
            FileDataSource(path="unexised_file").fetch()
        with pytest.raises(ValueError, match="cannot match proper format type for ddl"):
            FileDataSource(path="file.ddl")

        assert FileDataSource(path="1.json").format_type() == FormatType.Json
        assert FileDataSource(path="1.2.jsonl").format_type() == FormatType.Jsonl
        assert FileDataSource(path="1.csv").format_type() == FormatType.Csv
        assert FileDataSource(path="1.txt").format_type() == FormatType.Text
        assert FileDataSource(path=".1.json").format_type() == FormatType.Json
        f = FileDataSource(path="123")
        f.set_format_type(FormatType.Json)
        assert f.format_type() == FormatType.Json

    finally:
        os.remove("1.json")
        os.remove("1.2.jsonl")
        os.remove("1.csv")
        os.remove("1.txt")
        os.remove(".1.json")
        os.remove("123")


def test_read_from_folder():
    os.makedirs("test_dirs", exist_ok=True)
    os.makedirs("test_dirs/inner_test_dirs", exist_ok=True)
    with open("test_dirs/test_file1.txt", "w") as f:
        f.write("test_file1")

    with open("test_dirs/test_file2.txt", "w") as f:
        f.write("test_file2")

    with open("test_dirs/inner_test_dirs/test_file3.txt", "w") as f:
        f.write("test_file3")

    f = FileDataSource(path="test_dirs")
    content_list = f.fetch()
    content_list.sort()

    assert content_list == ["test_file1", "test_file2", "test_file3"]

    shutil.rmtree("test_dirs")


def test_save_to_folder():
    folder_path = "test_folder"
    file_name = "file.txt"

    try:
        os.makedirs(folder_path)

        f = FileDataSource(path=folder_path, file_format=FormatType.Text)
        f.save("this is a data")
        assert os.path.isdir(folder_path)
        for root, dirs, files in os.walk(folder_path):
            assert len(files) == 1

        file_content = "this is a data"

        f = FileDataSource(path=file_name)
        f.save(file_content)
        with open(file_name) as f:
            content = f.read()
            assert content == file_content

    finally:
        shutil.rmtree(folder_path)
        os.remove(file_name)


def test_save_as_folder():
    folder_path = "test_folder"

    try:
        f = FileDataSource(path=folder_path, save_as_folder=True)
        f.save(["file1", "file2"])
        for root, dirs, files in os.walk(folder_path):
            assert len(files) == 2
    finally:
        shutil.rmtree(folder_path)


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


def create_an_empty_qianfan_datasource() -> QianfanDataSource:
    return QianfanDataSource(
        id=1,
        group_id=2,
        name="test",
        set_type=DataSetType.TextOnly,
        project_type=DataProjectType.Conversation,
        template_type=DataTemplateType.NonSortedConversation,
        version=1,
        storage_type=DataStorageType.PrivateBos,
        storage_id="123",
        storage_path="456",
        storage_name="storage_name",
        storage_raw_path="/s/",
        storage_region="bj",
        data_format_type=FormatType.Jsonl,
    )


@patch("qianfan.dataset.data_source.get_bos_file_shared_url", return_value="url")
@patch("qianfan.dataset.data_source.upload_content_to_bos", return_value=None)
@patch("qianfan.dataset.data_source.upload_file_to_bos", return_value=None)
def test_qianfan_data_source_save(mocker: MockerFixture, *args, **kwargs):
    ds = create_an_empty_qianfan_datasource()
    with pytest.raises(
        ValueError, match="can't set 'data' and 'zip_file_path' simultaneously"
    ):
        ds.save("1", "2")

    with pytest.raises(ValueError, match="must set either 'data' or 'zip_file_path'"):
        ds.save()

    ds.storage_type = DataStorageType.PublicBos
    with pytest.raises(NotImplementedError):
        ds.save("1")

    ds = create_an_empty_qianfan_datasource()
    config = get_config()

    config.ACCESS_KEY = ""
    config.SECRET_KEY = ""

    assert not ds.save(
        "1", sup_storage_id="1", sup_storage_path="/sdasd/", sup_storage_region="bj"
    )
    ds.ak = "1"
    assert not ds.save("1")
    ds.sk = "2"
    assert ds.save("1")

    config.ACCESS_KEY = "1"
    config.SECRET_KEY = "2"

    assert ds.save(
        "1", sup_storage_id="1", sup_storage_path="/sdasd/", sup_storage_region="bj"
    )
    assert ds.save(
        zip_file_path="1",
        sup_storage_id="1",
        sup_storage_path="/sdasd/",
        sup_storage_region="bj",
    )


def test_qianfan_data_source_load():
    try:
        ds = create_an_empty_qianfan_datasource()
        content = ds.fetch()[0]
        assert len(json.loads(content, strict=False)) == 1
        content = ds.fetch()[0]
        assert json.loads(content, strict=False)[0]["response"] == [["no response"]]
    finally:
        shutil.rmtree(QianfanDatasetLocalCacheDir)
