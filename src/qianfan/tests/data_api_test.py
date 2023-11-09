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
    Unit test for Data
"""


from qianfan import Data
from qianfan.resources.console.consts import (
    DataExportDestinationType,
    DataProjectType,
    DataSetType,
    DataSourceType,
    DataStorageType,
    DataTemplateType,
)

enter_except_flag = True


def _check_and_reset_except_flag() -> bool:
    global enter_except_flag
    ret = enter_except_flag
    enter_except_flag = False
    return ret


def _enter_except_handle_block():
    global enter_except_flag
    enter_except_flag = True


def test_create_task():
    """
    test Data.create_bare_dataset
    """
    try:
        resp = Data.create_bare_dataset(
            "test_dataset_name",
            DataSetType.TextOnly,
            DataProjectType.Conversation,
            DataTemplateType.NonAnnotatedConversation,
            DataStorageType.PrivateBos,
        )
    except ValueError as e:
        _enter_except_handle_block()
        assert str(e) == "storage id is empty while create dataset in private bos"

    assert _check_and_reset_except_flag()

    try:
        resp = Data.create_bare_dataset(
            "test_dataset_name",
            DataSetType.MultiModel,
            DataProjectType.Conversation,
            DataTemplateType.NonAnnotatedConversation,
            DataStorageType.PublicBos,
        )
    except ValueError as e:
        _enter_except_handle_block()
        assert (
            str(e) == "Incompatible project type or template type with multi model set"
        )

    assert _check_and_reset_except_flag()

    try:
        resp = Data.create_bare_dataset(
            "test_dataset_name",
            DataSetType.TextOnly,
            DataProjectType.Conversation,
            DataTemplateType.QuerySet,
            DataStorageType.PublicBos,
        )
    except ValueError as e:
        _enter_except_handle_block()
        assert (
            str(e)
            == "Incompatible project type with template type when create text dataset"
        )

    assert _check_and_reset_except_flag()

    resp = Data.create_bare_dataset(
        "test_dataset_name",
        DataSetType.TextOnly,
        DataProjectType.Conversation,
        DataTemplateType.NonAnnotatedConversation,
        DataStorageType.PrivateBos,
        "bos_bucket_name",
        "bos_path",
    )

    reqs = resp.get("_request")
    assert reqs["versionId"] == 1
    assert reqs["templateType"] == DataTemplateType.NonAnnotatedConversation

    assert resp.get("result", {})

    resp = resp.get("result")
    assert resp.get("groupName", "") == "test_dataset_name"
    assert resp.get("projectType", 12) == DataProjectType.Conversation
    assert resp.get("storageInfo", {}).get("storageId", "") == "bos_bucket_name"
    assert resp.get("storageInfo", {}).get("rawStoragePath", "") == "bos_path"


def test_create_import_task():
    """
    test Data.create_data_import_task
    """
    try:
        Data.create_data_import_task(
            dataset_id=1,
            is_annotated=True,
            import_source=DataSourceType.PrivateBos,
            file_url="",
        )
    except ValueError as e:
        _enter_except_handle_block()
        assert str(e) == "import file url can't be empty"

    assert _check_and_reset_except_flag()

    _check_and_reset_except_flag()

    resp = Data.create_data_import_task(
        dataset_id=1,
        is_annotated=True,
        import_source=DataSourceType.SharedZipUrl,
        file_url="1",
    )

    reqs = resp.get("_request")
    assert reqs["datasetId"] == 1
    assert reqs["annotated"]

    assert resp.get("result", False)


def test_release_dataset():
    """
    test Data.release_dataset
    """
    resp = Data.release_dataset(12)
    reqs = resp.get("_request")

    assert reqs["datasetId"] == 12

    assert resp.get("log_id", "") == "log_id"


def test_get_dataset_info():
    """
    test Data.get_dataset_info
    """
    resp = Data.get_dataset_info(12)
    reqs = resp.get("_request")

    assert reqs["datasetId"] == 12

    assert resp.get("result", {})

    resp = resp.get("result")
    assert resp.get("versionInfo").get("datasetId") == 12


def test_get_dataset_status():
    """
    test Data.get_dataset_status_in_batch
    """
    resp = Data.get_dataset_status_in_batch([12, 48])
    reqs = resp.get("_request")

    assert reqs["datasetIds"] == "12,48"
    assert "12" in resp.get("result", {})
    assert "48" in resp.get("result", {})


def test_get_dataset_import_error_detail():
    """
    test Data.get_dataset_import_error_detail
    """
    resp = Data.get_dataset_import_error_detail(12, 55)
    reqs = resp.get("_request")

    assert reqs["datasetId"] == 12
    assert reqs["errCode"] == 55

    assert resp.get("log_id") == "log_id"


def test_delete_dataset():
    """
    test Data.delete_dataset
    """
    resp = Data.delete_dataset(12)
    reqs = resp.get("_request")

    assert reqs["datasetId"] == 12

    assert "versionCount" in resp.get("result")


def test_create_dataset_export_task():
    """
    test Data.create_dataset_export_task
    """
    try:
        resp = Data.create_dataset_export_task(
            dataset_id=12,
            export_destination_type=DataExportDestinationType.PrivateBos,
        )
    except ValueError as e:
        _enter_except_handle_block()
        assert str(e) == "storage id needed when export to private bos"

    assert _check_and_reset_except_flag()

    resp = Data.create_dataset_export_task(
        dataset_id=12,
        export_destination_type=DataExportDestinationType.PrivateBos,
        storage_id="bucket_name",
    )
    reqs = resp.get("_request")

    assert reqs["datasetId"] == 12
    assert reqs["exportFormat"] == 0
    assert reqs["exportType"] == 1
    assert reqs["exportTo"] == DataExportDestinationType.PrivateBos
    assert reqs["storageId"] == "bucket_name"

    assert resp.get("result")


def test_get_export_record():
    """
    test Data.get_dataset_export_records
    """
    resp = Data.get_dataset_export_records(12)
    reqs = resp.get("_request")

    assert reqs["datasetId"] == 12

    assert resp.get("result", [])[0].get("creatorName", "") == "yyw02"
