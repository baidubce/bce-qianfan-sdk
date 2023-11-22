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
import pytest

from qianfan.resources import Data
from qianfan.resources.console.consts import (
    DataExportDestinationType,
    DataProjectType,
    DataSetType,
    DataSourceType,
    DataStorageType,
    DataTemplateType,
    EntityListingType,
)


def test_create_task():
    """
    test Data.create_bare_dataset
    """
    with pytest.raises(
        ValueError, match="storage id is empty while create dataset in private bos"
    ):
        resp = Data.create_bare_dataset(
            "test_dataset_name",
            DataSetType.TextOnly,
            DataProjectType.Conversation,
            DataTemplateType.NonSortedConversation,
            DataStorageType.PrivateBos,
        )

    with pytest.raises(
        ValueError,
        match="Incompatible project type or template type with multi model set",
    ):
        resp = Data.create_bare_dataset(
            "test_dataset_name",
            DataSetType.MultiModel,
            DataProjectType.Conversation,
            DataTemplateType.NonSortedConversation,
            DataStorageType.PublicBos,
        )

    with pytest.raises(
        ValueError,
        match="Incompatible project type with template type when create text dataset",
    ):
        resp = Data.create_bare_dataset(
            "test_dataset_name",
            DataSetType.TextOnly,
            DataProjectType.Conversation,
            DataTemplateType.QuerySet,
            DataStorageType.PublicBos,
        )

    resp = Data.create_bare_dataset(
        "test_dataset_name",
        DataSetType.TextOnly,
        DataProjectType.Conversation,
        DataTemplateType.NonSortedConversation,
        DataStorageType.PrivateBos,
        "bos_bucket_name",
        "bos_path",
    )

    reqs = resp.get("_request")
    assert reqs["versionId"] == 1
    assert reqs["templateType"] == DataTemplateType.NonSortedConversation

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
    with pytest.raises(ValueError, match="import file url can't be empty"):
        Data.create_data_import_task(
            dataset_id=1,
            is_annotated=True,
            import_source=DataSourceType.PrivateBos,
            file_url="",
        )

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
    with pytest.raises(
        ValueError, match="storage id needed when export to private bos"
    ):
        resp = Data.create_dataset_export_task(
            dataset_id=12,
            export_destination_type=DataExportDestinationType.PrivateBos,
        )

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


def test_create_etl_task():
    """
    test Data.create_dataset_etl_task
    """
    resp = Data.create_dataset_etl_task(
        1, 2, {"clean": [], "filter": [], "deduplication": [], "desensitization": []}
    )
    reqs = resp.get("_request")

    assert reqs["sourceDatasetId"] == 1
    assert reqs["destDatasetId"] == 2
    assert reqs["entityType"] == 2
    assert isinstance(reqs["operationsV2"], dict)


def test_get_dataset_etl_task_info():
    """
    test Data.get_dataset_etl_task_info
    """

    resp = Data.get_dataset_etl_task_info(1)
    reqs = resp.get("_request")

    assert reqs["etlId"] == 1
    assert resp.body.get("result").get("id") == 1


def test_delete_dataset_etl_task():
    """
    test Data.delete_dataset_etl_task
    """

    resp = Data.delete_dataset_etl_task([12, 34])
    reqs = resp.get("_request")

    assert reqs["etlIds"] == [12, 34]


def test_create_dataset_augmenting_task():
    """
    test Data.create_dataset_augmenting_task
    """
    with pytest.raises(ValueError, match="num_seed_fewshot should be between 1 to 10"):
        Data.create_dataset_augmenting_task("1", 1, 2, "", "", 1, 90, 1, 1)

    with pytest.raises(
        ValueError, match="num_instances_to_generate should be between 1 to 5000"
    ):
        Data.create_dataset_augmenting_task("1", 1, 2, "", "", 1, 1, 5001, 1)

    with pytest.raises(
        ValueError, match="similarity_threshold should be between 0 to 1"
    ):
        Data.create_dataset_augmenting_task("1", 1, 2, "", "", 1, 1, 1, -1)

    resp = Data.create_dataset_augmenting_task(
        "test",
        12,
        34,
        "ERNIE-Bot-turbo",
        "https://aip.baidubce.com/rpc/2.0/ai_custom/v1/wenxinworkshop/chat/eb-instant",
        12,
        1,
        1,
        1,
    )
    reqs = resp.get("_request")

    assert reqs["name"] == "test"
    assert reqs["sourceDatasetId"] == 12
    assert reqs["destDatasetId"] == 34
    assert reqs["serviceName"] == "ERNIE-Bot-turbo"
    assert (
        reqs["serviceUrl"]
        == "https://aip.baidubce.com/rpc/2.0/ai_custom/v1/wenxinworkshop/chat/eb-instant"
    )
    assert reqs["appId"] == 12
    assert reqs["numSeedFewshot"] == 1
    assert reqs["numInstancesToGenerate"] == 1
    assert reqs["similarityThreshold"] == 1


def test_get_dataset_augmenting_task_info():
    """
    test Data.get_dataset_augmenting_task_info
    """

    resp = Data.get_dataset_augmenting_task_info(1)
    reqs = resp.get("_request")

    assert reqs["taskId"] == 1


def test_delete_dataset_augmenting_task():
    """
    test Data.delete_dataset_augmenting_task
    """

    resp = Data.delete_dataset_augmenting_task([1])
    reqs = resp.get("_request")

    assert reqs["taskIds"] == [1]


def test_annotate_an_entity():
    """
    test Data.annotate_an_entity
    """

    resp = Data.annotate_an_entity(
        "gbd", 12, [{"prompt": "test", "response": [["test"]]}]
    )
    reqs = resp.get("_request")

    assert reqs["id"] == "gbd"
    assert reqs["datasetId"] == 12
    assert reqs["content"] == [{"prompt": "test", "response": [["test"]]}]


def test_delete_an_entity():
    """
    test Data.delete_an_entity
    """

    resp = Data.delete_an_entity(["12"], 12)
    reqs = resp.get("_request")

    assert reqs["id"] == ["12"]
    assert reqs["datasetId"] == 12


def test_list_all_entity_in_dataset():
    """
    test Data.list_all_entity_in_dataset
    """

    with pytest.raises(ValueError):
        Data.list_all_entity_in_dataset(1, 2, 3, [1], None)

    with pytest.raises(ValueError):
        Data.list_all_entity_in_dataset(1, 2, 3, None, [2])

    resp = Data.list_all_entity_in_dataset(1, 2, 3)
    reqs = resp.get("_request")

    assert reqs["datasetId"] == 1
    assert reqs["offset"] == 2
    assert reqs["pageSize"] == 3
    assert reqs["tabType"] == EntityListingType.All.value
