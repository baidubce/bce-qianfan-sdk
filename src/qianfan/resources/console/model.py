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
Model API
"""

from typing import Any, Dict, List, Optional

from qianfan.consts import Consts
from qianfan.resources.console.utils import console_api_request
from qianfan.resources.typing import QfRequest


class Model(object):
    """
    Class for Model Management API
    """

    @classmethod
    @console_api_request
    def list(cls, model_id: int, **kwargs: Any) -> QfRequest:
        """
        List all versions and source information of a model.

        This class method is used to retrieve information about all versions of a
        specific model, along with their source details.

        Parameters:
          model_id (int):
            The unique identifier of the model for which you want to list versions.
          kwargs (Any):
            Additional keyword arguments that can be passed to customize the request.

        Note:
        The `@console_api_request` decorator is applied to this method, enabling it to
        send the generated QfRequest and return a QfResponse to the user.

        API Doc: https://cloud.baidu.com/doc/WENXINWORKSHOP/s/clnlizwcs
        """
        req = QfRequest(method="POST", url=Consts.ModelDetailAPI)
        req.json_body = {"modelId": model_id, **kwargs}
        return req

    @classmethod
    @console_api_request
    def detail(cls, model_version_id: int, **kwargs: Any) -> QfRequest:
        """
        Retrieve detailed information for a specific model version.

        This method is used to fetch detailed information about a particular model
        version identified by the `model_version_id` parameter. The information
        includes various attributes and properties associated with the specified
        model version.

        Parameters:
          model_version_id (int):
            The unique identifier for the model version whose details are to be
            retrieved.
          kwargs (Any):
            Additional keyword arguments that can be passed to customize the request.

        Note:
        The `@console_api_request` decorator is applied to this method, enabling it to
        send the generated QfRequest and return a QfResponse to the user.

        API Doc: https://cloud.baidu.com/doc/WENXINWORKSHOP/s/ylnljj3ku
        """
        req = QfRequest(method="POST", url=Consts.ModelVersionDetailAPI)
        req.json_body = {"modelVersionId": model_version_id, **kwargs}
        return req

    @classmethod
    @console_api_request
    def publish(
        cls,
        is_new: bool,
        version_meta: Dict[str, Any],
        model_name: Optional[str] = None,
        model_id: Optional[int] = None,
        tags: Optional[List[str]] = None,
        **kwargs: Any,
    ) -> QfRequest:
        """
        Publishes a trained model to the model repository.

        This function allows for the publishing of a trained model to a model
        repository.

        Parameters:
          is_new (bool):
            A boolean indicating whether this is a new model to be published.
          version_meta (Dict[str, Any]):
            Metadata for the model being published.
          model_name (Optional[str]):
            The name of the model to be published (required when `is_new` is True).
          model_id (Optional[int]):
            The ID of the model to be published (required when `is_new` is False).
          tags (Optional[List[str]]):
            A list of tags associated with the model (optional).
          kwargs (Any):
            Additional keyword arguments that can be passed to customize the request.

        Note:
        The `@console_api_request` decorator is applied to this method, enabling it to
        send the generated QfRequest and return a QfResponse to the user.

        API Doc: https://cloud.baidu.com/doc/WENXINWORKSHOP/s/Jlnlm0rdx
        """
        req = QfRequest(method="POST", url=Consts.ModelPublishAPI)
        req.json_body = {"isNewModel": is_new, "versionMeta": version_meta, **kwargs}
        if model_name is not None:
            req.json_body["modelName"] = model_name
        if model_id is not None:
            req.json_body["modelId"] = model_id
        if tags is not None:
            req.json_body["tags"] = tags
        return req

    @classmethod
    @console_api_request
    def create_evaluation_task(
        cls,
        name: str,
        version_info: List[Dict[str, Any]],
        dataset_id: int,
        eval_config: Dict[str, Any],
        description: Optional[str] = None,
        pending_eval_id: Optional[int] = None,
        **kwargs: Any,
    ) -> QfRequest:
        """
        Create an evaluation task on model(s) with dataset

        Parameters:
            name (str):
                the evaluation name you want to use
            version_info (List[Dict[str, Any]]):
                a list of model info which will be evaluated
            dataset_id (int):
                dataset's id for evaluation
            eval_config (Dict[str, Any]):
                the detail info about how to conduct this evaluation
            description (Optional[str]):
                description about evaluation, default to None.
            pending_eval_id (Optional[int]):
                the id of evaluation which doesn't start yet,
                you can set this parameter to modify the spec of
                specific evaluation and start it. Default to None
            **kwargs (Any):
                arbitrary arguments

        Note:
        The `@console_api_request` decorator is applied to this method, enabling it to
        send the generated QfRequest and return a QfResponse to the user.

        API Doc: https://cloud.baidu.com/doc/WENXINWORKSHOP/s/Hlpbyhl9o
        """
        req = QfRequest(method="POST", url=Consts.ModelEvalCreateAPI)
        request_json = {
            "name": name,
            "versionEvalInfo": version_info,
            "datasetId": dataset_id,
            "evalStandardConf": eval_config,
            "computeResourceConf": {"vmType": 1, "vmNumber": 8},
        }

        if "dataset_name" in kwargs:
            request_json["datasetName"] = kwargs["dataset_name"]

        if pending_eval_id:
            request_json["id"] = pending_eval_id

        if description:
            request_json["description"] = description

        req.json_body = request_json
        return req

    @classmethod
    @console_api_request
    def get_evaluation_info(
        cls,
        eval_id: int,
        **kwargs: Any,
    ) -> QfRequest:
        """
        Get an evaluation task info

        Parameters:
            eval_id (int):
                the id of evaluation you want to check
            **kwargs (Any):
                arbitrary arguments

        Note:
        The `@console_api_request` decorator is applied to this method, enabling it to
        send the generated QfRequest and return a QfResponse to the user.

        API Doc: https://cloud.baidu.com/doc/WENXINWORKSHOP/s/wlpbyj1dn
        """
        req = QfRequest(method="POST", url=Consts.ModelEvalInfoAPI)
        req.json_body = {"id": eval_id}

        return req

    @classmethod
    @console_api_request
    def get_evaluation_result(
        cls,
        eval_id: int,
        **kwargs: Any,
    ) -> QfRequest:
        """
        Get the result of an evaluation

        Parameters:
            eval_id (int):
                the id of evaluation you want to check
            **kwargs (Any):
                arbitrary arguments

        Note:
        The `@console_api_request` decorator is applied to this method, enabling it to
        send the generated QfRequest and return a QfResponse to the user.

        API Doc: https://cloud.baidu.com/doc/WENXINWORKSHOP/s/7lpbyk8fj
        """
        req = QfRequest(method="POST", url=Consts.ModelEvalResultAPI)
        req.json_body = {"id": eval_id}

        return req

    @classmethod
    @console_api_request
    def stop_evaluation_task(
        cls,
        eval_id: int,
        **kwargs: Any,
    ) -> QfRequest:
        """
        Stop an evaluation task

        Parameters:
            eval_id (int):
                the id of evaluation you want to stop
            **kwargs (Any):
                arbitrary arguments

        Note:
        The `@console_api_request` decorator is applied to this method, enabling it to
        send the generated QfRequest and return a QfResponse to the user.

        API Doc: https://cloud.baidu.com/doc/WENXINWORKSHOP/s/klpbyl1ea
        """
        req = QfRequest(method="POST", url=Consts.ModelEvalStopAPI)
        req.json_body = {"id": eval_id}

        return req
