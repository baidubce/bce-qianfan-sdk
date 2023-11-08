from qianfan import Data
from qianfan.resources.console.user_constant import *


def test_create_task():
    try:
        resp = Data.create_bare_dataset(
            "test_dataset_name",
            DataSetType.TextOnly,
            DataProjectType.Conversation,
            DataTemplateType.NonAnnotatedConversation,
            DataStorageType.PrivateBos,
        )
    except ValueError as e:
        assert str(e) == "storage id is empty while create dataset in private bos"

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
    try:
        Data.create_data_import_task(
            dataset_id=1,
            is_annotated=True,
            import_source=DataSourceType.Local,
            files_url=[],
        )
    except ValueError as e:
        assert str(e) == "import file url can't be empty"

    try:
        Data.create_data_import_task(
            dataset_id=1,
            is_annotated=True,
            import_source=DataSourceType.PrivateBos,
            files_url=["1", "2"],
        )
    except ValueError as e:
        assert str(e) == "import file apart from local can only have 1 file url"

    resp = Data.create_data_import_task(
            dataset_id=1,
            is_annotated=True,
            import_source=DataSourceType.PrivateBos,
            files_url=["1"],
        )

    reqs = resp.get("_request")
    assert reqs["datasetId"] == 1
    assert reqs["annotated"]

    assert resp.get("result", False)


def test_release_dataset():
    resp = Data.release_dataset(12)
    reqs = resp.get("_request")

    assert reqs["datasetId"] == 12

    assert resp.get("log_id", "") == "log_id"


def test_get_dataset_info():
    resp = Data.get_dataset_info(12)
    reqs = resp.get("_request")

    assert reqs["datasetId"] == 12

    assert resp.get("result", {})

    resp = resp.get("result")
    assert resp.get("versionInfo").get("datasetId") == 12


def test_get_dataset_status():
    resp = Data.get_dataset_status_in_batch([12, 48])
    reqs = resp.get("_request")

    assert reqs["datasetIds"] == "12,48"
    assert "12" in resp.get("result", {})
    assert "48" in resp.get("result", {})


def test_get_dataset_import_error_detail():
    resp = Data.get_dataset_error_detail(12, 55)
    reqs = resp.get("_request")

    assert reqs["datasetId"] == 12
    assert reqs["errCode"] == 55

    assert resp.get("log_id") == "log_id"


def test_delete_dataset():
    resp = Data.delete_dataset(12)
    reqs = resp.get("_request")

    assert reqs["datasetId"] == 12

    assert "versionCount" in resp.get("result")


def test_create_dataset_export_task():
    try:
        resp = Data.create_dataset_export_task(
            dataset_id=12,
            export_scene=DataExportScene.Normal,
            export_destination_type=DataSourceType.SharedZipUrl,
        )
    except ValueError as e:
        assert str(e) == "could not import to DataSourceType.SharedZipUrl"

    try:
        resp = Data.create_dataset_export_task(
            dataset_id=12,
            export_scene=DataExportScene.Normal,
            export_destination_type=DataSourceType.PrivateBos,
        )
    except ValueError as e:
        assert str(e) == "storage id needed when export to private bos"

    resp = Data.create_dataset_export_task(
        dataset_id=12,
        export_scene=DataExportScene.Normal,
        export_destination_type=DataSourceType.PrivateBos,
        storage_id="bucket_name"
    )
    reqs = resp.get("_request")

    assert reqs["datasetId"] == 12
    assert reqs["exportFormat"] == -1
    assert reqs["exportType"] == 1
    assert reqs["exportScene"] == DataExportScene.Normal
    assert reqs["exportTo"] == DataSourceType.PrivateBos
    assert reqs["storageId"] == "bucket_name"

    assert resp.get("result")


def test_get_export_record():
    resp = Data.get_dataset_export_records(12)
    reqs = resp.get("_request")

    assert reqs["datasetId"] == 12

    assert resp.get("result", [])[0].get("creatorName", "") == "yyw02"
