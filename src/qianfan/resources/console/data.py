from typing import Any, Dict, List, Optional

from qianfan.consts import Consts
from qianfan.resources.console.user_constant import (
    DataExportScene,
    DataProjectType,
    DataSetType,
    DataSourceType,
    DataStorageType,
    DataTemplateType,
    DataZipInnerContentFormatType,
)
from qianfan.resources.console.utils import console_api_request
from qianfan.resources.typing import QfRequest


class Data:
    @classmethod
    @console_api_request
    def create_bare_dataset(
        cls,
        name: str,
        data_set_type: DataSetType,
        project_type: DataProjectType,
        template_type: DataTemplateType,
        storage_type: DataStorageType,
        storage_id: Optional[str] = None,
        storage_path: Optional[str] = None,
        **kwargs: Any,
    ) -> QfRequest:
        if DataSetType == DataSetType.MultiModel and (
            project_type != DataProjectType.Text2Speech
            or template_type != DataTemplateType.Text2Speech
        ):
            raise ValueError(
                "Incompatible project type or template type with multi model set"
            )

        str_project_type = str(project_type)
        str_template_type = str(template_type)
        if not str_template_type.startswith(str_project_type):
            raise ValueError(
                "Incompatible project type with template type when create text dataset"
            )

        req = QfRequest(method="POST", url=Consts.DatasetCreateAPI)
        post_body_dict = {
            "name": name,
            "versionId": 1,
            "projectType": project_type,
            "templateType": template_type,
            "dataType": data_set_type,
            "storageType": storage_type,
        }

        if storage_type == DataStorageType.PrivateBos:
            if not storage_id:
                raise ValueError(
                    "storage id is empty while create dataset in private bos"
                )
            if not storage_path:
                raise ValueError(
                    "storage path is empty while create dataset in private bos"
                )
            post_body_dict["storageId"] = storage_id
            post_body_dict["rawStoragePath"] = storage_path

        req.json_body = post_body_dict
        return req

    @classmethod
    @console_api_request
    def release_dataset(cls, dataset_id: int, **kwargs: Any) -> QfRequest:
        req = QfRequest(method="POST", url=Consts.DatasetReleaseAPI)
        req.json_body = {
            "datasetId": dataset_id,
        }

        return req

    @classmethod
    @console_api_request
    def create_data_import_task(
        cls,
        dataset_id: int,
        is_annotated: bool,
        import_source: DataSourceType,
        files_url: List[str],
        zip_format: DataZipInnerContentFormatType = DataZipInnerContentFormatType.Json,
        is_removing_duplicated_data: bool = True,
        **kwargs: Any,
    ) -> QfRequest:
        req = QfRequest(method="POST", url=Consts.DatasetImportAPI)
        post_body_dict: Dict[str, Any] = {
            "datasetId": dataset_id,
            "annotated": is_annotated,
            "importFrom": import_source,
            "removeDuplicate": is_removing_duplicated_data,
            "zipFormat": zip_format,
        }

        if not files_url:
            raise ValueError("import file url can't be empty")
        if import_source != DataSourceType.Local and len(files_url) != 1:
            raise ValueError("import file apart from local can only have 1 file url")
        post_body_dict["files"] = files_url

        req.json_body = post_body_dict
        return req

    @classmethod
    @console_api_request
    def get_dataset_info(cls, dataset_id: int, **kwargs: Any) -> QfRequest:
        req = QfRequest(method="POST", url=Consts.DatasetInfoAPI)
        req.json_body = {
            "datasetId": dataset_id,
        }

        return req

    @classmethod
    @console_api_request
    def get_dataset_status_in_batch(
        cls, dataset_id_list: List[int], **kwargs: Any
    ) -> QfRequest:
        int_dataset_id_list: List[str] = [str(id) for id in dataset_id_list]
        ids = ",".join(int_dataset_id_list)

        req = QfRequest(method="POST", url=Consts.DatasetStatusFetchInBatchAPI)
        req.json_body = {
            "datasetIds": ids,
        }

        return req

    @classmethod
    @console_api_request
    def create_dataset_export_task(
        cls,
        dataset_id: int,
        export_scene: DataExportScene,
        export_destination_type: DataSourceType,
        storage_id: Optional[str] = None,
        is_export_origin_files_only: bool = True,
        is_export_with_annotation: bool = True,
        **kwargs: Any,
    ) -> QfRequest:
        req = QfRequest(method="POST", url=Consts.DatasetExportAPI)
        post_body_dict: Dict[str, Any] = {
            "datasetId": dataset_id,
            "exportFormat": -1 if is_export_origin_files_only else 0,
            "exportType": 1 if is_export_with_annotation else 2,
            "exportScene": export_scene,
            "exportTo": export_destination_type,
        }

        if export_destination_type == DataSourceType.SharedZipUrl:
            raise ValueError("could not import to DataSourceType.SharedZipUrl")
        if export_destination_type == DataSourceType.PrivateBos:
            if not storage_id:
                raise ValueError("storage id needed when export to private bos")
            post_body_dict["storageId"] = storage_id

        req.json_body = post_body_dict
        return req

    @classmethod
    @console_api_request
    def delete_dataset(cls, dataset_id: int, **kwargs: Any) -> QfRequest:
        req = QfRequest(method="POST", url=Consts.DatasetDeleteAPI)
        req.json_body = {
            "datasetId": dataset_id,
        }

        return req

    @classmethod
    @console_api_request
    def get_dataset_export_records(cls, dataset_id: int, **kwargs: Any) -> QfRequest:
        req = QfRequest(method="POST", url=Consts.DatasetExportRecordAPI)
        req.json_body = {
            "datasetId": dataset_id,
        }

        return req

    @classmethod
    @console_api_request
    def get_dataset_error_detail(
        cls, dataset_id: int, error_code: int, **kwargs: Any
    ) -> QfRequest:
        req = QfRequest(method="POST", url=Consts.DatasetImportErrorDetail)
        req.json_body = {
            "datasetId": dataset_id,
            "errCode": error_code,
        }

        return req
