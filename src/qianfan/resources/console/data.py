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
Data API
"""

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
    """
    Class for Data API
    """

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
        """
        create a bare dataset。

        Parameters:
            name (str):
                the name of the dataset.
            data_set_type (DataSetType):
                the type of the dataset.
            project_type (DataProjectType):
                the project type.
            template_type (DataTemplateType):
                the template type.
            storage_type (DataStorageType):
                the type of data storage.
            storage_id (Optional[str]):
                the storage ID when the storage type is PrivateBos.
            storage_path (Optional[str]):
                the storage path when the storage type is PrivateBos.
            **kwargs:
                any other parameters.

        Note:
            The `@console_api_request` decorator is applied to this method,
            enabling it to send the generated QfRequest
            and return a QfResponse to the user.

        API Doc: https://cloud.baidu.com/doc/WENXINWORKSHOP/s/qloic44vr
        """
        if DataSetType == DataSetType.MultiModel and (
            project_type != DataProjectType.Text2Speech
            or template_type != DataTemplateType.Text2Speech
        ):
            raise ValueError(
                "Incompatible project type or template type with multi model set"
            )

        str_project_type = str(project_type.value)
        str_template_type = str(template_type.value)
        if not str_template_type.startswith(str_project_type):
            raise ValueError(
                "Incompatible project type with template type when create text dataset"
            )

        req = QfRequest(method="POST", url=Consts.DatasetCreateAPI)
        post_body_dict = {
            "name": name,
            "versionId": 1,
            "projectType": project_type.value,
            "templateType": template_type.value,
            "dataType": data_set_type.value,
            "storageType": storage_type.value,
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
        """
        release dataset

        Parameters:
            dataset_id (int):
                dataset id.
            **kwargs:
                any other parameters.

        Note:
            The `@console_api_request` decorator is applied to this method,
            enabling it to send the generated QfRequest
            and return a QfResponse to the user.

        API Doc: https://cloud.baidu.com/doc/WENXINWORKSHOP/s/Uloic6krs
        """
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
        """
        create data import task

        Parameters:
            dataset_id (int):
                dataset id
            is_annotated (bool):
                has dataset been annotated
            import_source (DataSourceType):
                the source for importing dataset
            files_url (List[str]):
                file url list
            zip_format (Optional[DataZipInnerContentFormatType]):
                data format in zip, default to json
            is_removing_duplicated_data (Optional[bool]):
                is removing duplicate data needed
            **kwargs:
                any other parameters.

        Note:
            The `@console_api_request` decorator is applied to this method,
            enabling it to send the generated QfRequest
            and return a QfResponse to the user.

        API Doc: https://cloud.baidu.com/doc/WENXINWORKSHOP/s/Yloic82qy
        """
        req = QfRequest(method="POST", url=Consts.DatasetImportAPI)
        post_body_dict: Dict[str, Any] = {
            "datasetId": dataset_id,
            "annotated": is_annotated,
            "importFrom": import_source.value,
            "removeDuplicate": is_removing_duplicated_data,
            "zipFormat": zip_format.value,
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
        """
        get dataset info

        Parameters:
            dataset_id (int):
                dataset id.
            **kwargs:
                any other parameters.

        Note:
            The `@console_api_request` decorator is applied to this method,
            enabling it to send the generated QfRequest
            and return a QfResponse to the user.

        API Doc: https://cloud.baidu.com/doc/WENXINWORKSHOP/s/Xloick80a
        """
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
        """
        get dataset status in dataset id list

        Parameters:
            dataset_id_list (List[int]):
                dataset id list.
            **kwargs:
                any other parameters.

        Note:
            The `@console_api_request` decorator is applied to this method,
            enabling it to send the generated QfRequest
            and return a QfResponse to the user.

        API Doc: https://cloud.baidu.com/doc/WENXINWORKSHOP/s/Sloicm9qz
        """
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
        """
        create dataset export task

        Args:
            dataset_id (int):
                dataset id
            export_scene (DataExportScene):
                when data export happen
            export_destination_type (DataSourceType):
                export destination type, and it can't be SharedZipUrl here,
                 or a ValueError will be raised
            storage_id (Optional[str]):
                storage id of user's BOS,
                needed when export_destination_type is PrivateBos, Default to None.
            is_export_origin_files_only (Optional[bool]):
                is export origin files in dataset only, Defaults to True.
            is_export_with_annotation (Optional[bool]):
                is export dataset with annotation, Defaults to True.
            **kwargs:
                any other parameters.

        Note:
            The `@console_api_request` decorator is applied to this method,
            enabling it to send the generated QfRequest
            and return a QfResponse to the user.

        API Doc: https://cloud.baidu.com/doc/WENXINWORKSHOP/s/bloicnydp
        """
        req = QfRequest(method="POST", url=Consts.DatasetExportAPI)
        post_body_dict: Dict[str, Any] = {
            "datasetId": dataset_id,
            "exportFormat": -1 if is_export_origin_files_only else 0,
            "exportType": 1 if is_export_with_annotation else 2,
            "exportScene": export_scene.value,
            "exportTo": export_destination_type.value,
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
        """
        delete dataset

        Parameters:
            dataset_id (int):
                dataset id.
            **kwargs:
                any other parameters.

        Note:
            The `@console_api_request` decorator is applied to this method,
            enabling it to send the generated QfRequest
            and return a QfResponse to the user.

        API Doc: https://cloud.baidu.com/doc/WENXINWORKSHOP/s/Oloicp6fk
        """
        req = QfRequest(method="POST", url=Consts.DatasetDeleteAPI)
        req.json_body = {
            "datasetId": dataset_id,
        }

        return req

    @classmethod
    @console_api_request
    def get_dataset_export_records(cls, dataset_id: int, **kwargs: Any) -> QfRequest:
        """
        get dataset export records

        Parameters:
            dataset_id (int):
                dataset id.
            **kwargs:
                any other parameters.

        Note:
            The `@console_api_request` decorator is applied to this method,
            enabling it to send the generated QfRequest
            and return a QfResponse to the user.

        API Doc: https://cloud.baidu.com/doc/WENXINWORKSHOP/s/Zlonqgtw0
        """
        req = QfRequest(method="POST", url=Consts.DatasetExportRecordAPI)
        req.json_body = {
            "datasetId": dataset_id,
        }

        return req

    @classmethod
    @console_api_request
    def get_dataset_import_error_detail(
        cls, dataset_id: int, error_code: int, **kwargs: Any
    ) -> QfRequest:
        """
        get dataset status in dataset id list

        Parameters:
            dataset_id (int):
                dataset id.
            error_code (int):
                error code used to query
            **kwargs:
                any other parameters.

        Note:
            The `@console_api_request` decorator is applied to this method,
            enabling it to send the generated QfRequest
            and return a QfResponse to the user.

        API Doc: https://cloud.baidu.com/doc/WENXINWORKSHOP/s/hlonqulbq
        """
        req = QfRequest(method="POST", url=Consts.DatasetImportErrorDetail)
        req.json_body = {
            "datasetId": dataset_id,
            "errCode": error_code,
        }

        return req
