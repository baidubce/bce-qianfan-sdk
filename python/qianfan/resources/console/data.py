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
import functools
from typing import Any, Callable, Dict, List, Optional, Union

from qianfan.consts import Consts
from qianfan.errors import QianfanError
from qianfan.resources.console.consts import (
    V2 as V2Consts,
)
from qianfan.resources.console.consts import (
    DataExportDestinationType,
    DataProjectType,
    DataSetType,
    DataSourceType,
    DataStorageType,
    DataTemplateType,
    EntityListingType,
)
from qianfan.resources.console.utils import _get_console_v2_query, console_api_request
from qianfan.resources.typing import ParamSpec, QfRequest, QfResponse
from qianfan.utils import log_error

P = ParamSpec("P")


def _data_api_exception_handler(f: Callable[P, QfResponse]) -> Callable[P, QfResponse]:
    """the error code checker for data api only"""

    @functools.wraps(f)
    def inner(*args: Any, **kwargs: Any) -> QfResponse:
        resp = f(*args, **kwargs)
        if resp["status"] == 400 or not resp["success"]:
            code = resp.body["code"]
            message = resp["message"]
            err_msg = f"request error with code: {code} , and message: {message}"
            log_error(err_msg)
            raise QianfanError(err_msg)
        return resp

    return inner


class Data:
    """
    Class for Data API
    """

    @classmethod
    @_data_api_exception_handler
    @console_api_request
    def create_bare_dataset(
        cls,
        name: str,
        data_set_type: DataSetType,
        project_type: DataProjectType,
        template_type: DataTemplateType,
        storage_type: DataStorageType = DataStorageType.PublicBos,
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
        if data_set_type == DataSetType.MultiModel and (
            project_type != DataProjectType.Text2Image
            or template_type != DataTemplateType.Text2Image
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

            # 此 path 必须以 / 结尾，为了防止用户没有加上，这里特判
            if storage_path[-1] != "/":
                storage_path += "/"

            post_body_dict["storageId"] = storage_id
            post_body_dict["rawStoragePath"] = storage_path

        req.json_body = post_body_dict
        return req

    @classmethod
    @_data_api_exception_handler
    @console_api_request
    def release_dataset(cls, dataset_id: str, **kwargs: Any) -> QfRequest:
        """
        release dataset

        Parameters:
            dataset_id (str):
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
    @_data_api_exception_handler
    @console_api_request
    def create_data_import_task(
        cls,
        dataset_id: str,
        is_annotated: bool,
        import_source: DataSourceType,
        file_url: str,
        **kwargs: Any,
    ) -> QfRequest:
        """
        create data import task

        Parameters:
            dataset_id (str):
                dataset id
            is_annotated (bool):
                has dataset been annotated
            import_source (DataSourceType):
                the source for importing dataset
            file_url (str):
                file url
            **kwargs:
                any other parameters.

        Note:
            The `@console_api_request` decorator is applied to this method,
            enabling it to send the generated QfRequest
            and return a QfResponse to the user.

        API Doc: https://cloud.baidu.com/doc/WENXINWORKSHOP/s/Yloic82qy
        """
        if not file_url:
            raise ValueError("import file url can't be empty")

        req = QfRequest(method="POST", url=Consts.DatasetImportAPI)
        post_body_dict: Dict[str, Any] = {
            "datasetId": dataset_id,
            "annotated": is_annotated,
            "importFrom": import_source.value,
            "files": [file_url],
        }

        req.json_body = post_body_dict
        return req

    @classmethod
    @_data_api_exception_handler
    @console_api_request
    def get_dataset_info(cls, dataset_id: str, **kwargs: Any) -> QfRequest:
        """
        get dataset info

        Parameters:
            dataset_id (str):
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
    @_data_api_exception_handler
    @console_api_request
    def get_dataset_status_in_batch(
        cls, dataset_id_list: List[str], **kwargs: Any
    ) -> QfRequest:
        """
        get dataset status in dataset id list

        Parameters:
            dataset_id_list (List[str]):
                dataset id list.
            **kwargs:
                any other parameters.

        Note:
            The `@console_api_request` decorator is applied to this method,
            enabling it to send the generated QfRequest
            and return a QfResponse to the user.

        API Doc: https://cloud.baidu.com/doc/WENXINWORKSHOP/s/Sloicm9qz
        """

        req = QfRequest(method="POST", url=Consts.DatasetStatusFetchInBatchAPI)
        req.json_body = {
            "datasetIds": dataset_id_list,
        }

        return req

    @classmethod
    @_data_api_exception_handler
    @console_api_request
    def create_dataset_export_task(
        cls,
        dataset_id: str,
        export_destination_type: DataExportDestinationType,
        storage_id: Optional[str] = None,
        is_export_with_annotation: bool = True,
        **kwargs: Any,
    ) -> QfRequest:
        """
        create dataset export task

        Args:
            dataset_id (str):
                dataset id
            export_destination_type (DataExportDestinationType):
                export destination type
            storage_id (Optional[str]):
                storage id of user's BOS,
                needed when export_destination_type is PrivateBos, Default to None.
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
            "exportFormat": 0,
            "exportType": 1 if is_export_with_annotation else 2,
            "exportTo": export_destination_type.value,
        }

        if export_destination_type == DataExportDestinationType.PrivateBos:
            if not storage_id:
                raise ValueError("storage id needed when export to private bos")
            post_body_dict["storageId"] = storage_id

        req.json_body = post_body_dict
        return req

    @classmethod
    @_data_api_exception_handler
    @console_api_request
    def delete_dataset(cls, dataset_id: str, **kwargs: Any) -> QfRequest:
        """
        delete dataset

        Parameters:
            dataset_id (str):
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
    @_data_api_exception_handler
    @console_api_request
    def get_dataset_export_records(cls, dataset_id: str, **kwargs: Any) -> QfRequest:
        """
        get dataset export records

        Parameters:
            dataset_id (str):
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
    @_data_api_exception_handler
    @console_api_request
    def get_dataset_import_error_detail(
        cls, dataset_id: str, error_code: int, **kwargs: Any
    ) -> QfRequest:
        """
        get dataset status in dataset id list

        Parameters:
            dataset_id (str):
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

    @classmethod
    @_data_api_exception_handler
    @console_api_request
    def create_dataset_etl_task(
        cls,
        etl_task_name: str,
        source_dataset_id: str,
        destination_dataset_id: str,
        operations: Dict[str, List[Dict[str, Any]]],
        **kwargs: Any,
    ) -> QfRequest:
        """
        create a post-pretrain dataset etl task

        Parameters:
            etl_task_name (str):
                etl task name
            source_dataset_id (str):
                dataset id need to be processed.
            destination_dataset_id (str):
                where dataset should be stored after etl
            operations (Dict[str, List[Dict[str, Any]]]),
                etl operator settings.
            **kwargs (Any):
                any other parameters.

        Note:
            The `@console_api_request` decorator is applied to this method,
            enabling it to send the generated QfRequest
            and return a QfResponse to the user.

        API Doc: https://cloud.baidu.com/doc/WENXINWORKSHOP/s/8lp6irqen
        """
        req = QfRequest(method="POST", url=Consts.DatasetCreateETLTaskAPI)
        req.json_body = {
            "etlTaskName": etl_task_name,
            "sourceDatasetId": source_dataset_id,
            "destDatasetId": destination_dataset_id,
            "entityType": 2,
            "operationsV2": operations,
        }

        return req

    @classmethod
    @_data_api_exception_handler
    @console_api_request
    def get_dataset_etl_task_info(cls, etl_id: str, **kwargs: Any) -> QfRequest:
        """
        get a post-pretrain dataset etl task info

        Parameters:
            etl_id (str):
                dataset etl task id.
            **kwargs (Any):
                any other parameters.

        Note:
            The `@console_api_request` decorator is applied to this method,
            enabling it to send the generated QfRequest
            and return a QfResponse to the user.

        API Doc: https://cloud.baidu.com/doc/WENXINWORKSHOP/s/mlp6it4vd
        """
        req = QfRequest(method="POST", url=Consts.DatasetETLTaskInfoAPI)
        req.json_body = {
            "etlId": etl_id,
        }

        return req

    @classmethod
    @_data_api_exception_handler
    @console_api_request
    def get_dataset_etl_task_list(
        cls, page_size: int = 10, offset: int = 0, **kwargs: Any
    ) -> QfRequest:
        """
        get a post-pretrain dataset etl task info

        Parameters:
            page_size (int):
                the length of etl list showing, default to 10.
            offset (int):
                where to start list etl task, default to 0.
            **kwargs (Any):
                any other parameters.

        Note:
            The `@console_api_request` decorator is applied to this method,
            enabling it to send the generated QfRequest
            and return a QfResponse to the user.

        API Doc: https://cloud.baidu.com/doc/WENXINWORKSHOP/s/elp7myxvp
        """
        req = QfRequest(method="POST", url=Consts.DatasetETLListTaskAPI)
        req.json_body = {
            "offset": offset,
            "pageSize": page_size,
        }

        return req

    @classmethod
    @_data_api_exception_handler
    @console_api_request
    def delete_dataset_etl_task(cls, etl_ids: List[str], **kwargs: Any) -> QfRequest:
        """
        delete post-pretrain dataset etl task

        Parameters:
            etl_ids (List[str]):
                dataset etl task id list.
            **kwargs (Any):
                any other parameters.

        Note:
            The `@console_api_request` decorator is applied to this method,
            enabling it to send the generated QfRequest
            and return a QfResponse to the user.

        API Doc: https://cloud.baidu.com/doc/WENXINWORKSHOP/s/Glp6iu8ny
        """
        req = QfRequest(method="POST", url=Consts.DatasetETLTaskDeleteAPI)
        req.json_body = {
            "etlIds": etl_ids,
        }

        return req

    @classmethod
    @_data_api_exception_handler
    @console_api_request
    def create_dataset_augmenting_task(
        cls,
        name: str,
        source_dataset_id: str,
        destination_dataset_id: str,
        dev_api_id: str,
        app_id: int,
        num_seed_fewshot: int,
        num_instances_to_generate: int,
        similarity_threshold: float,
        **kwargs: Any,
    ) -> QfRequest:
        """
        create a data augmenting task

        Parameters:
            name (str):
                name of augment task
            source_dataset_id (str):
                dataset id need to be augmented.
            destination_dataset_id (str):
                where dataset should be stored after augmentation
            dev_api_id (str):
                fixed field with value depends on service_name.
            app_id (int):
                app id
            num_seed_fewshot (int):
                the number of sample used for augmenting each data
            num_instances_to_generate (int):
                the number of instance to generate
            similarity_threshold (float):
                similarity threshold
            **kwargs (Any):
                any other parameters.

        Note:
            The `@console_api_request` decorator is applied to this method,
            enabling it to send the generated QfRequest
            and return a QfResponse to the user.

        API Doc: https://cloud.baidu.com/doc/WENXINWORKSHOP/s/Dlp6iv0zw
        """
        if not (1 <= num_seed_fewshot <= 10):
            raise ValueError("num_seed_fewshot should be between 1 to 10")
        if not (1 <= num_instances_to_generate <= 5000):
            raise ValueError("num_instances_to_generate should be between 1 to 5000")
        if not (0 <= similarity_threshold <= 1):
            raise ValueError("similarity_threshold should be between 0 to 1")

        req = QfRequest(method="POST", url=Consts.DatasetCreateAugTaskAPI)
        req.json_body = {
            "name": name,
            "isSelfInstruct": True,
            "sourceDatasetId": source_dataset_id,
            "destDatasetId": destination_dataset_id,
            "devApiId": dev_api_id,
            "appId": app_id,
            "numSeedFewshot": num_seed_fewshot,
            "numInstancesToGenerate": num_instances_to_generate,
            "similarityThreshold": similarity_threshold,
        }

        return req

    @classmethod
    @_data_api_exception_handler
    @console_api_request
    def get_dataset_aug_task_list(
        cls,
        keyword: Optional[str] = None,
        sorted_by_start_time_asc: Optional[bool] = None,
        page_size: int = 10,
        offset: int = 0,
        **kwargs: Any,
    ) -> QfRequest:
        """
        get a post-pretrain dataset etl task info

        Parameters:
            keyword: (Optional[str]):
                optional keyword to search augmentation task, default to None.
            sorted_by_start_time_asc (Optional[bool]):
                is result list sorted by starting time in ascending order if True,
                sorted by starting time in descending order if False,
                sorted by id in ascending order if None.
                default to None
            page_size (int):
                the length of etl list showing, default to 10.
            offset (int):
                where to start list etl task, default to 0.
            **kwargs (Any):
                any other parameters.

        Note:
            The `@console_api_request` decorator is applied to this method,
            enabling it to send the generated QfRequest
            and return a QfResponse to the user.

        API Doc: https://cloud.baidu.com/doc/WENXINWORKSHOP/s/Flp7n9xmp
        """
        req = QfRequest(method="POST", url=Consts.DatasetAugListTaskAPI)
        request_json: Dict[str, Any] = {
            "isSelfInstruct": True,
            "offset": offset,
            "pageSize": page_size,
        }

        if keyword:
            request_json["word"] = keyword
        if sorted_by_start_time_asc is not None:
            request_json["sortField"] = "startTime"
            request_json["sortBy"] = "asc" if sorted_by_start_time_asc else "desc"

        req.json_body = request_json
        return req

    @classmethod
    @_data_api_exception_handler
    @console_api_request
    def get_dataset_augmenting_task_info(cls, task_id: str, **kwargs: Any) -> QfRequest:
        """
        get a data augmenting task info

        Parameters:
            task_id (str):
                dataset augmenting task id.
            **kwargs (Any):
                any other parameters.

        Note:
            The `@console_api_request` decorator is applied to this method,
            enabling it to send the generated QfRequest
            and return a QfResponse to the user.

        API Doc: https://cloud.baidu.com/doc/WENXINWORKSHOP/s/Clp6iwiy9
        """
        req = QfRequest(method="POST", url=Consts.DatasetAugTaskInfoAPI)
        req.json_body = {
            "taskId": task_id,
        }

        return req

    @classmethod
    @_data_api_exception_handler
    @console_api_request
    def delete_dataset_augmenting_task(
        cls, task_ids: List[str], **kwargs: Any
    ) -> QfRequest:
        """
        delete dataset augmenting task

        Parameters:
            task_ids (List[str]):
                dataset augmenting task id list.
            **kwargs (Any):
                any other parameters.

        Note:
            The `@console_api_request` decorator is applied to this method,
            enabling it to send the generated QfRequest
            and return a QfResponse to the user.

        API Doc: https://cloud.baidu.com/doc/WENXINWORKSHOP/s/glp6iy6h3
        """
        req = QfRequest(method="POST", url=Consts.DatasetAugTaskDeleteAPI)
        req.json_body = {
            "taskIds": task_ids,
        }

        return req

    @classmethod
    @_data_api_exception_handler
    @console_api_request
    def annotate_an_entity(
        cls,
        entity_id: str,
        dataset_id: str,
        content: Optional[List[Dict[str, Any]]] = None,
        labels: Optional[List[Dict[str, Any]]] = None,
        **kwargs: Any,
    ) -> QfRequest:
        """
        annotate an entity within a dataset

        Parameters:
            entity_id (str):
                entity id to be annotating
            dataset_id (str):
                dataset id to do annotate
            content (Optional[Dict[str, Any]]):
                the prompt and LLM responses on a conversation
            labels (Optional[Dict[str, Any]]):
                description of an image
            **kwargs (Any):
                any other parameters.

        Note:
            The `@console_api_request` decorator is applied to this method,
            enabling it to send the generated QfRequest
            and return a QfResponse to the user.

        API Doc: https://cloud.baidu.com/doc/WENXINWORKSHOP/s/mlp6izcqr
        """
        req = QfRequest(method="POST", url=Consts.DatasetAnnotateAPI)
        request_json: Dict[str, Any] = {
            "id": entity_id,
            "datasetId": dataset_id,
        }

        if content:
            request_json["content"] = content
        elif labels:
            request_json["labels"] = labels
        req.json_body = request_json

        return req

    @classmethod
    @_data_api_exception_handler
    @console_api_request
    def delete_an_entity(
        cls, entity_ids: List[str], dataset_id: str, **kwargs: Any
    ) -> QfRequest:
        """
        delete an entity from dataset

        Parameters:
            entity_ids (List[str]):
                entity id list
            dataset_id (str):
                dataset id to do delete

        Note:
            The `@console_api_request` decorator is applied to this method,
            enabling it to send the generated QfRequest
            and return a QfResponse to the user.

        API Doc: https://cloud.baidu.com/doc/WENXINWORKSHOP/s/ilp6j1rse
        """
        req = QfRequest(method="POST", url=Consts.DatasetEntityDeleteAPI)
        req.json_body = {"id": entity_ids, "datasetId": dataset_id}

        return req

    @classmethod
    @_data_api_exception_handler
    @console_api_request
    def list_all_entity_in_dataset(
        cls,
        dataset_id: str,
        offset: int = 0,
        page_size: int = 20,
        import_time_closure: Optional[List[int]] = None,
        annotating_time_closure: Optional[List[int]] = None,
        listing_type: EntityListingType = EntityListingType.All,
        label_id_str: Optional[str] = None,
        **kwargs: Any,
    ) -> QfRequest:
        """
        delete an entity from dataset

        Parameters:
            dataset_id (str):
                dataset id
            offset (int):
                offset of dataset where the list start, default to 0
            page_size (int):
                window size of the list, default to 20,
                the maximum value is 30 and the minimum is 1
            import_time_closure (Optional[List[int]]):
                a list containing start timestamp
                and end timestamp of importing time, default to None
            annotating_time_closure (Optional[List[int]]):
                a list containing start timestamp
                and end timestamp of annotating time, default to None
            listing_type (EntityListingType):
                type of listing, default to EntityListingType.All
            label_id_str (Optional[str]):
                label id of text2image, default to None

        Note:
            The `@console_api_request` decorator is applied to this method,
            enabling it to send the generated QfRequest
            and return a QfResponse to the user.

        API Doc: https://cloud.baidu.com/doc/WENXINWORKSHOP/s/Ulp6j2yep
        """
        req = QfRequest(method="POST", url=Consts.DatasetEntityListAPI)
        request_json: Dict[str, Any] = {
            "datasetId": dataset_id,
            "offset": offset,
            "pageSize": page_size,
            "tabType": listing_type.value,
        }

        if import_time_closure:
            if len(import_time_closure) != 2:
                raise ValueError(
                    f"the length of import_time_closure is {len(import_time_closure)},"
                    " rather than 2"
                )
            request_json["importTime"] = import_time_closure
        if annotating_time_closure:
            if len(annotating_time_closure) != 2:
                raise ValueError(
                    "the length of annotating_time_closure is"
                    f" {len(annotating_time_closure)}, rather than 2"
                )
            request_json["annoTime"] = annotating_time_closure
        if label_id_str:
            request_json["labelId"] = label_id_str

        req.json_body = request_json
        return req

    @classmethod
    @console_api_request
    def create_offline_batch_inference_task(
        cls,
        name: str,
        input_bos_uri: Optional[str] = None,
        output_bos_uri: Optional[str] = None,
        model_id: Optional[str] = None,
        endpoint: Optional[str] = None,
        inference_params: Dict[str, Any] = {},
        description: Optional[str] = None,
        afs_config: Optional[Dict[str, Any]] = None,
        completion_window: Optional[str] = None,
        **kwargs: Any,
    ) -> QfRequest:
        """
        Create an offline batch inference task

        Parameters:
            name (str):
                Name of the batch inference task
            model_id (Optional[str]):
                model id of the model to be used for inference.
            endpoint (str):
                Endpoint of the model to be used for inference.
            input_bos_uri (str):
                BOS URI of the input data
            output_bos_uri (str):
                BOS URI of the output data
            inference_params (Dict[str, Any]):
                The inference parameters used in the model
            description (Optional[str]):
                Description of the batch inference task
            completion_window (Optional[str]):
                The Running Time Limitation. Currently it can only
                be "24h" or None. Default to None

        Note:
            The `@console_api_request` decorator is applied to this method,
            enabling it to send the generated QfRequest
            and return a QfResponse to the user.
        """
        req = QfRequest(
            method="POST",
            url=Consts.DatasetV2OfflineBatchInferenceAPI,
            query=_get_console_v2_query(
                Consts.DatasetCreateOfflineBatchInferenceAction
            ),
            headers={"Referer": "infer"},
        )
        request_json: Dict[str, Any] = {
            "name": name,
            "inferenceParams": inference_params,
            **kwargs,
        }
        if afs_config:
            request_json["afsConfig"] = afs_config
        elif input_bos_uri and output_bos_uri:
            request_json["inputBosUri"] = input_bos_uri
            request_json["outputBosUri"] = output_bos_uri
        else:
            raise ValueError(
                "Either afs_config or input_bos_uri and output_bos_uri must be"
                " provided."
            )

        if model_id:
            request_json["modelId"] = model_id
        elif endpoint:
            request_json["endpoint"] = endpoint

        if description is not None:
            request_json["description"] = description

        if completion_window is not None:
            request_json["completion_window"] = completion_window

        req.json_body = request_json
        return req

    @classmethod
    @console_api_request
    def get_offline_batch_inference_task(
        cls,
        task_id: str,
        **kwargs: Any,
    ) -> QfRequest:
        """
        Get detail of an offline batch inference task

        Parameters:
            task_id (str):
                Id of the batch inference task

        Note:
            The `@console_api_request` decorator is applied to this method,
            enabling it to send the generated QfRequest
            and return a QfResponse to the user.
        """
        req = QfRequest(
            method="POST",
            url=Consts.DatasetV2OfflineBatchInferenceAPI,
            query=_get_console_v2_query(
                Consts.DatasetDescribeOfflineBatchInferenceAction
            ),
        )
        request_json: Dict[str, Any] = {
            "taskId": task_id,
            **kwargs,
        }

        req.json_body = request_json
        return req

    @classmethod
    @console_api_request
    def stop_offline_batch_inference_task(
        cls,
        task_id: str,
        **kwargs: Any,
    ) -> QfRequest:
        """
        Delete an offline batch inference task

        Parameters:
            task_id (str):
                Id of the batch inference task

        Note:
            The `@console_api_request` decorator is applied to this method,
            enabling it to send the generated QfRequest
            and return a QfResponse to the user.
        """
        req = QfRequest(
            method="POST",
            url=Consts.DatasetV2OfflineBatchInferenceAPI,
            query=_get_console_v2_query(Consts.DatasetStopOfflineBatchInferenceAction),
        )
        request_json: Dict[str, Any] = {
            "taskId": task_id,
            **kwargs,
        }

        req.json_body = request_json
        return req

    @classmethod
    @console_api_request
    def list_offline_batch_inference_task(
        cls,
        marker: Optional[str] = None,
        max_keys: Optional[int] = None,
        page_reverse: Optional[bool] = None,
        run_status: Optional[Union[List[str], str]] = None,
        **kwargs: Any,
    ) -> QfRequest:
        """
        get batch_inference list .

        Parameters:
        marker: Optional[str] = None,
            job_id, the marker of the first page.
        max_keys: Optional[int] = None,
            max keys of the page.
        page_reverse: Optional[bool] = None,
            page reverse or not.
        run_status: Optional[List[str]] = None,
            run status of the batch inference task.
            'Running', 'Done', 'Stopped', 'Failed'
        Note:
            The `@console_api_request` decorator is applied to this method,
            enabling it to send the generated QfRequest
            and return a QfResponse to the user.
        """
        req = QfRequest(
            method="POST",
            url=Consts.DatasetV2OfflineBatchInferenceAPI,
            query=_get_console_v2_query(
                Consts.DatasetDescribeOfflineBatchInferencesAction
            ),
        )
        if isinstance(run_status, str):
            run_status = [run_status]
        elif run_status is None:
            run_status = []
        else:
            run_status = list(run_status)
        req.json_body = {
            k: v
            for k, v in {
                **kwargs,
                "marker": marker,
                "maxKeys": max_keys,
                "pageReverse": page_reverse,
                "runStatus": run_status,
            }.items()
            if v is not None
        }
        return req

    class V2:
        @classmethod
        def base_api_route(cls) -> str:
            """
            base api url route for dataset V2.

            Returns:
                str: base api url route
            """
            return Consts.DatasetV2BaseRouteAPI

        @classmethod
        @console_api_request
        def create_dataset(
            cls,
            dataset_name: str,
            dataset_format: V2Consts.DatasetFormat,
            storage_type: V2Consts.StorageType,
            storage_path: Optional[str] = None,
            **kwargs: Any,
        ) -> QfRequest:
            """
            create dataset.

            Parameters:
                dataset_name (str):
                    dataset name.
                dataset_format (V2Consts.DatasetFormat):
                    dataset format.
                storage_type (V2Consts.StorageType):
                    storage type.
                storage_path (Optional[str], optional):
                    storage path. Defaults to None.

            Note:
                The `@console_api_request` decorator is applied to this method,
                enabling it to send the generated QfRequest
                and return a QfResponse to the user.
            """
            post_body_dict = {
                "datasetName": dataset_name,
                "dataFormat": dataset_format.value,
                "storageType": storage_type.value,
            }

            if storage_path:
                if storage_path[-1] != "/":
                    storage_path += "/"

                post_body_dict["storagePath"] = storage_path

            req = QfRequest(
                method="POST",
                url=cls.base_api_route(),
                query=_get_console_v2_query(Consts.DatasetV2CreateDatasetAction),
            )
            req.json_body = post_body_dict

            return req

        @classmethod
        @console_api_request
        def get_dataset_list(
            cls,
            marker: Optional[str] = None,
            max_keys: int = 10,
            page_reverse: bool = False,
            filter: Optional[Dict[str, Any]] = None,
            **kwargs: Any,
        ) -> QfRequest:
            """
            get dataset list.

            Parameters:
                marker (Optional[str], optional):
                    marker of the first page. Defaults to None.
                max_keys (int, optional):
                    max keys of the page. Defaults to 10.
                page_reverse (bool, optional):
                    page reverse or not. Defaults to False.
                filter (Optional[Dict[str, Any]], optional):
                    filter conditions. Defaults to None.

            Note:
                The `@console_api_request` decorator is applied to this method,
                enabling it to send the generated QfRequest
                and return a QfResponse to the user.
            """
            post_json_body: Dict[str, Any] = {
                "maxKeys": max_keys,
                "pageReverse": page_reverse,
            }

            if marker:
                post_json_body["marker"] = marker

            if filter:
                post_json_body["filter"] = filter

            req = QfRequest(
                method="POST",
                url=cls.base_api_route(),
                query=_get_console_v2_query(Consts.DatasetV2GetDatasetListAction),
            )
            req.json_body = post_json_body

            return req

        @classmethod
        @console_api_request
        def delete_dataset(
            cls,
            dataset_id: str,
            **kwargs: Any,
        ) -> QfRequest:
            """
            delete dataset.

            Parameters:
                dataset_id (str):
                    dataset id.

            Note:
                The `@console_api_request` decorator is applied to this method,
                enabling it to send the generated QfRequest
                and return a QfResponse to the user.
            """

            post_body_dict = {
                "datasetId": dataset_id,
            }

            req = QfRequest(
                method="POST",
                url=cls.base_api_route(),
                query=_get_console_v2_query(Consts.DatasetV2DeleteDatasetAction),
            )
            req.json_body = post_body_dict

            return req

        @classmethod
        @console_api_request
        def create_dataset_version(
            cls,
            dataset_id: str,
            description: Optional[str] = None,
            **kwargs: Any,
        ) -> QfRequest:
            """
            create dataset version.

            Parameters:
                dataset_id (str):
                    dataset id.
                description (Optional[str], optional):
                    dataset version description. Defaults to None.

            Note:
                The `@console_api_request` decorator is applied to this method,
                enabling it to send the generated QfRequest
                and return a QfResponse to the user.
            """
            post_body_dict = {
                "datasetId": dataset_id,
            }

            if description:
                post_body_dict["description"] = description

            req = QfRequest(
                method="POST",
                url=cls.base_api_route(),
                query=_get_console_v2_query(Consts.DatasetV2CreateDatasetVersionAction),
            )
            req.json_body = post_body_dict

            return req

        @classmethod
        @console_api_request
        def get_dataset_version_info(
            cls,
            version_id: str,
            **kwargs: Any,
        ) -> QfRequest:
            """
            get dataset version info.

            Parameters:
                version_id (str):
                    dataset version id.

            Note:
                The `@console_api_request` decorator is applied to this method,
                enabling it to send the generated QfRequest
                and return a QfResponse to the user.
            """

            post_body_dict = {
                "versionId": version_id,
            }

            req = QfRequest(
                method="POST",
                url=cls.base_api_route(),
                query=_get_console_v2_query(
                    Consts.DatasetV2GetDatasetVersionInfoAction
                ),
            )
            req.json_body = post_body_dict

            return req

        @classmethod
        @console_api_request
        def delete_dataset_version(
            cls,
            version_id: str,
            **kwargs: Any,
        ) -> QfRequest:
            """
            delete dataset version.

            Parameters:
                version_id (str):
                    dataset version id.

            Note:
                The `@console_api_request` decorator is applied to this method,
                enabling it to send the generated QfRequest
                and return a QfResponse to the user.
            """

            post_body_dict = {
                "versionId": version_id,
            }

            req = QfRequest(
                method="POST",
                url=cls.base_api_route(),
                query=_get_console_v2_query(Consts.DatasetV2DeleteDatasetVersionAction),
            )
            req.json_body = post_body_dict

            return req

        @classmethod
        @console_api_request
        def publish_dataset_version(
            cls,
            version_id: str,
            **kwargs: Any,
        ) -> QfRequest:
            """
            publish dataset version.

            Parameters:
                version_id (str):
                    dataset version id.

            Note:
                The `@console_api_request` decorator is applied to this method,
                enabling it to send the generated QfRequest
                and return a QfResponse to the user.
            """

            post_body_dict = {
                "versionId": version_id,
            }

            req = QfRequest(
                method="POST",
                url=cls.base_api_route(),
                query=_get_console_v2_query(
                    Consts.DatasetV2PublishDatasetVersionAction
                ),
            )
            req.json_body = post_body_dict

            return req

        @classmethod
        @console_api_request
        def get_dataset_version_list(
            cls,
            dataset_id: str,
            marker: Optional[str] = None,
            max_keys: int = 10,
            page_reverse: bool = False,
            filter: Optional[Dict[str, Any]] = None,
            **kwargs: Any,
        ) -> QfRequest:
            """
            get dataset version list.

            Parameters:
                dataset_id (str):
                    dataset id.
                marker (Optional[str], optional):
                    marker. Defaults to None.
                max_keys (int, optional):
                    max keys. Defaults to 10.
                page_reverse (bool, optional):
                    page reverse. Defaults to False.
                filter (Optional[Dict[str, Any]], optional):
                    filter. Defaults to None.

            Note:
                The `@console_api_request` decorator is applied to this method,
                enabling it to send the generated QfRequest
                and return a QfResponse to the user.
            """

            post_body_dict = {
                "datasetId": dataset_id,
                "maxKeys": max_keys,
                "pageReverse": page_reverse,
            }

            if marker:
                post_body_dict["marker"] = marker

            if filter:
                post_body_dict["filter"] = filter

            req = QfRequest(
                method="POST",
                url=cls.base_api_route(),
                query=_get_console_v2_query(
                    Consts.DatasetV2GetDatasetVersionListAction
                ),
            )
            req.json_body = post_body_dict

            return req

        @classmethod
        @console_api_request
        def create_dataset_version_import_task(
            cls,
            version_id: str,
            files: List[str],
            **kwargs: Any,
        ) -> QfRequest:
            """
            create dataset version import task.

            Parameters:
                version_id (str):
                    dataset version id.
                files (List[str]):
                    file paths.

            Note:
                The `@console_api_request` decorator is applied to this method,
                enabling it to send the generated QfRequest
                and return a QfResponse to the user.
            """

            post_body_dict = {
                "versionId": version_id,
                "files": files,
            }

            req = QfRequest(
                method="POST",
                url=cls.base_api_route(),
                query=_get_console_v2_query(
                    Consts.DatasetV2CreateDatasetVersionImportTaskAction
                ),
            )
            req.json_body = post_body_dict

            return req

        @classmethod
        @console_api_request
        def get_dataset_version_import_task_info(
            cls,
            task_id: str,
            **kwargs: Any,
        ) -> QfRequest:
            """
            get dataset version import task info.

            Parameters:
                task_id (str):
                    task id.

            Note:
                The `@console_api_request` decorator is applied to this method,
                enabling it to send the generated QfRequest
                and return a QfResponse to the user.
            """

            post_body_dict = {
                "taskId": task_id,
            }

            req = QfRequest(
                method="POST",
                url=cls.base_api_route(),
                query=_get_console_v2_query(
                    Consts.DatasetV2GetDatasetVersionImportTaskInfoAction
                ),
            )
            req.json_body = post_body_dict

            return req

        @classmethod
        @console_api_request
        def create_dataset_version_export_task(
            cls,
            version_id: str,
            storage_type: V2Consts.StorageType,
            storage_path: Optional[str] = None,
            **kwargs: Any,
        ) -> QfRequest:
            """
            create dataset version export task.

            Parameters:
                version_id (str):
                    dataset version id.
                storage_type (V2Consts.StorageType):
                    storage type.
                storage_path (Optional[str], optional):
                    storage path. Defaults to None.

            Note:
                The `@console_api_request` decorator is applied to this method,
                enabling it to send the generated QfRequest
                and return a QfResponse to the user.
            """

            post_body_dict = {
                "versionId": version_id,
                "storageType": storage_type.value,
            }

            if storage_path:
                post_body_dict["storagePath"] = storage_path

            req = QfRequest(
                method="POST",
                url=cls.base_api_route(),
                query=_get_console_v2_query(
                    Consts.DatasetV2CreateDatasetVersionExportTaskAction
                ),
            )
            req.json_body = post_body_dict

            return req

        @classmethod
        @console_api_request
        def get_dataset_version_export_task_info(
            cls,
            task_id: str,
            **kwargs: Any,
        ) -> QfRequest:
            """
            get dataset version export task info.

            Parameters:
                task_id (str):
                    task id.

            Note:
                The `@console_api_request` decorator is applied to this method,
                enabling it to send the generated QfRequest
                and return a QfResponse to the user.
            """

            post_body_dict = {
                "taskId": task_id,
            }

            req = QfRequest(
                method="POST",
                url=cls.base_api_route(),
                query=_get_console_v2_query(
                    Consts.DatasetV2GetDatasetVersionExportTaskInfoAction
                ),
            )
            req.json_body = post_body_dict

            return req
