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
FineTune API
"""

from typing import Any, Dict, Optional

from qianfan.consts import Consts
from qianfan.resources.console.utils import console_api_request
from qianfan.resources.typing import QfRequest


class FineTune(object):
    """
    Class for FineTune API
    """

    @classmethod
    @console_api_request
    def get_job(cls, task_id: int, job_id: int, **kwargs: Any) -> QfRequest:
        """
        Retrieves a job for model fine-tuning.

        This method is responsible for retrieving a job for the specified fine-tuning
        task and job IDs.

        Parameters:
          task_id (int):
            The ID of the task associated with the fine-tuning job.
          job_id (int):
            The ID of the fine-tuning job to retrieve.
          kwargs (Any):
            Additional keyword arguments that can be passed to customize the request.

        Note:
        The `@console_api_request` decorator is applied to this method, enabling it to
        send the generated QfRequest and return a QfResponse to the user.

        API Doc: https://cloud.baidu.com/doc/WENXINWORKSHOP/s/wlmrgowee
        """
        req = QfRequest(method="POST", url=Consts.FineTuneGetJobAPI)
        req.json_body = {"taskId": task_id, "jobId": job_id, **kwargs}
        return req

    @classmethod
    @console_api_request
    def create_task(
        cls,
        name: str,
        base_train_type: str,
        train_type: str,
        description: Optional[str] = None,
        **kwargs: Any
    ) -> QfRequest:
        """
        Create a model fine-tuning task.

        This function is used to create a model fine-tuning task. The task can be
        customized with a name and description.

        Parameters:
          name (str):
            The name of the fine-tuning task.
          description (Optional[str]):
            An optional description for the fine-tuning task.
          kwargs (Any):
            Additional keyword arguments that can be passed to customize the request.

        Note:
        The `@console_api_request` decorator is applied to this method, enabling it to
        send the generated QfRequest and return a QfResponse to the user.

        API Doc: https://cloud.baidu.com/doc/WENXINWORKSHOP/s/almrgn397
        """
        req = QfRequest(method="POST", url=Consts.FineTuneCreateTaskAPI)
        req.json_body = {
            "name": name,
            "baseTrainType": base_train_type,
            "trainType": train_type,
            **kwargs,
        }
        if description is not None:
            req.json_body["description"] = description
        return req

    @classmethod
    @console_api_request
    def create_job(cls, job: Dict[str, Any], **kwargs: Any) -> QfRequest:
        """
        Create a job for fine-tuning a model.

        This function creates a job for fine-tuning a model.

        Parameters:
          job (Dict[str, Any]):
            A dictionary containing job details and configurations. The fields are same
            with the API doc.
          kwargs (Any):
            Additional keyword arguments that can be passed to customize the request.

        Note:
        The `@console_api_request` decorator is applied to this method, enabling it to
        send the generated QfRequest and return a QfResponse to the user.

        API Doc: https://cloud.baidu.com/doc/WENXINWORKSHOP/s/mlmrgo4yx
        """
        req = QfRequest(method="POST", url=Consts.FineTuneCreateJobAPI)
        req.json_body = {**job, **kwargs}
        return req

    @classmethod
    @console_api_request
    def stop_job(cls, task_id: int, job_id: int, **kwargs: Any) -> QfRequest:
        """
        Stop a fine-tuning job.

        This function allows the stopping of a fine-tuning job associated with a
        specific task.

        Parameters:
          task_id (int):
            The identifier of the task associated with the fine-tuning job.
          job_id (int):
            The identifier of the fine-tuning job to be stopped.
          kwargs:
            Additional keyword arguments that can be passed to customize the request.

        Note:
        The `@console_api_request` decorator is applied to this method, enabling it to
        send the generated QfRequest and return a QfResponse to the user.

        API Doc: https://cloud.baidu.com/doc/WENXINWORKSHOP/s/2lnlebz15
        """
        req = QfRequest(method="POST", url=Consts.FineTuneStopJobAPI)
        req.json_body = {"taskId": task_id, "jobId": job_id, **kwargs}
        return req
