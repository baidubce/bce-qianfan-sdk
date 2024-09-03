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
from typing import List
from unittest.mock import patch

import pytest
from pytest_mock import MockerFixture

from qianfan import get_config
from qianfan.dataset import Dataset
from qianfan.dataset.consts import (
    QianfanDatasetPackColumnName,
    QianfanLocalCacheDir,
)
from qianfan.dataset.data_source import FileDataSource, FormatType, QianfanDataSource
from qianfan.resources.console.consts import (
    DataProjectType,
    DataSetType,
    DataStorageType,
    DataTemplateType,
)


def _clean_func():
    try:
        shutil.rmtree(QianfanLocalCacheDir)
    except Exception:
        return


@pytest.fixture(autouse=True, scope="function")
def clean_cache():
    _clean_func()
    yield
    _clean_func()


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
        with pytest.raises(FileNotFoundError):
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
    content_list = f.fetch(using_file_as_element=True).to_pydict()[
        QianfanDatasetPackColumnName
    ]
    content_list.sort()

    assert content_list == ["test_file1", "test_file2", "test_file3"]

    shutil.rmtree("test_dirs")


def test_save_to_folder():
    folder_path = "test_folder"
    file_name = "file.txt"

    try:
        os.makedirs(folder_path)
        table = Dataset.create_from_pyobj(
            {QianfanDatasetPackColumnName: ["this is a data"]}
        )

        f = FileDataSource(
            path=folder_path, file_format=FormatType.Text, save_as_folder=True
        )
        f.save(table)
        assert os.path.isdir(folder_path)
        for root, dirs, files in os.walk(folder_path):
            assert len(files) == 1

        f = FileDataSource(path=file_name)
        f.save(table)
        with open(file_name) as f:
            content = f.read()
            assert content == "this is a data\n"

    finally:
        shutil.rmtree(folder_path)
        os.remove(file_name)


def test_save_as_folder():
    folder_path = "test_folder"

    try:
        table = Dataset.create_from_pyobj(
            {QianfanDatasetPackColumnName: ["file1", "file2"]}
        )
        f = FileDataSource(path=folder_path, save_as_folder=True)
        f.save(table)
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
    assert datasource_2.format_type() == FormatType.Text2Image


def test_create_qianfan_data_source_from_existed():
    source = QianfanDataSource.get_existed_dataset("12", False)
    assert source.id == "12"
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


@patch(
    "qianfan.utils.bos_uploader.BosHelper.get_bos_file_shared_url", return_value="url"
)
@patch("qianfan.utils.bos_uploader.BosHelper.upload_content_to_bos", return_value=None)
@patch("qianfan.utils.bos_uploader.BosHelper.upload_file_to_bos", return_value=None)
def test_qianfan_data_source_save(mocker: MockerFixture, *args, **kwargs):
    empty_table = Dataset.create_from_pyobj({QianfanDatasetPackColumnName: ["1"]})
    ds = create_an_empty_qianfan_datasource()

    ds.storage_type = DataStorageType.PublicBos
    with pytest.raises(NotImplementedError):
        ds.save(empty_table)

    ds = create_an_empty_qianfan_datasource()
    config = get_config()

    config.ACCESS_KEY = ""
    config.SECRET_KEY = ""

    with pytest.raises(ValueError):
        ds.save(
            empty_table,
            sup_storage_id="1",
            sup_storage_path="/sdasd/",
            sup_storage_region="bj",
        )

    ds.ak = "1"

    with pytest.raises(ValueError):
        ds.save(empty_table)

    ds.sk = "2"
    assert ds.save(empty_table)

    config.ACCESS_KEY = "1"
    config.SECRET_KEY = "2"

    assert ds.save(
        empty_table,
        sup_storage_id="1",
        sup_storage_path="/sdasd/",
        sup_storage_region="bj",
    )
    assert ds.save(
        empty_table,
        sup_storage_id="1",
        sup_storage_path="/sdasd/",
        sup_storage_region="bj",
    )


def test_qianfan_data_source_load():
    ds = create_an_empty_qianfan_datasource()
    content = Dataset(inner_table=ds.fetch()).list()
    assert content[0][0]["response"] == [["no response"]]


def test_save_to_file_data_source_json():
    test_json_file = "test_file.json"

    fake_data = [
        {"test_column1": 1, "test_column2": "2"},
        {"test_column1": 1, "test_column2": "2"},
    ]
    ds = Dataset.create_from_pyobj(fake_data)

    ds.save(data_file=test_json_file)
    with open(test_json_file, mode="r") as f:
        data = json.load(f)
        assert data == fake_data

    try:
        os.remove(test_json_file)
    except Exception:
        ...


def test_save_to_file_data_source_jsonl():
    test_jsonl_file = "test_file.jsonl"

    fake_data1 = [
        {"test_column1": 1, "test_column2": "2"},
        {"test_column1": 1, "test_column2": "2"},
    ]
    fake_data2 = [
        [
            {"test_column1": 1, "test_column2": "2"},
            {"test_column1": 1, "test_column2": "2"},
        ],
        [
            {"test_column1": 1, "test_column2": "2"},
            {"test_column1": 1, "test_column2": "2"},
        ],
    ]

    def read_jsonline_file(path) -> List:
        result = []
        with open(path, mode="r") as f:
            line = f.readline()
            while line:
                result.append(json.loads(line))
                line = f.readline()

        return result

    # 测试不用千帆格式写字典列表
    ds = Dataset.create_from_pyobj(fake_data1)

    ds.save(data_file=test_jsonl_file)
    result = read_jsonline_file(test_jsonl_file)
    assert result == fake_data1

    # 测试用千帆格式写字典列表
    ds.save(data_file=test_jsonl_file, use_qianfan_special_jsonl_format=True)
    result = read_jsonline_file(test_jsonl_file)
    assert isinstance(result[0], list)
    assert result[0][0] == fake_data1[0] and result[1][0] == fake_data1[1]

    # 测试用符合千帆的数据集写格式
    ds = Dataset.create_from_pyobj(fake_data2)

    ds.save(data_file=test_jsonl_file)
    result = read_jsonline_file(test_jsonl_file)
    assert result == fake_data2

    # 测试用千帆格式再加参数写列表
    ds = Dataset.create_from_pyobj(fake_data2)

    ds.save(data_file=test_jsonl_file, use_qianfan_special_jsonl_format=True)
    result = read_jsonline_file(test_jsonl_file)
    assert result == fake_data2

    try:
        os.remove(test_jsonl_file)
    except Exception:
        ...


def test_save_to_file_data_source_csv():
    test_csv_file = "test_file.csv"
    fake_data = [
        {"test_column1": "1", "test_column2": "n2"},
        {"test_column1": "1", "test_column2": "n2"},
    ]

    ds = Dataset.create_from_pyobj(fake_data)

    ds.save(data_file=test_csv_file)

    try:
        os.remove(test_csv_file)
    except Exception:
        ...
