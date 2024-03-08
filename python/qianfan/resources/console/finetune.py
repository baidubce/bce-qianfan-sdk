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

from typing import Any, Dict, Optional, Union

from qianfan.consts import Consts
from qianfan.resources.console import consts as console_consts
from qianfan.resources.console.utils import _get_console_v2_query, console_api_request
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
        **kwargs: Any,
    ) -> QfRequest:
        """
        Create a model fine-tuning task.

        This function is used to create a model fine-tuning task. The task can be
        customized with a name and description.

        Parameters:
          name (str):
            The name of the fine-tuning task.
          base_train_type (str):
            The base training type of the fine-tuning task. e.g. "ERNIE-Bot-turbo"
          train_type (str):
            The training type of the fine-tuning task. e.g. "ERNIE-Bot-turbo-0922
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
    def stop_job(cls, task_id: str, job_id: str, **kwargs: Any) -> QfRequest:
        """
        Stop a fine-tuning job.

        This function allows the stopping of a fine-tuning job associated with a
        specific task.

        Parameters:
          task_id (str):
            The identifier of the task associated with the fine-tuning job.
          job_id (str):
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

    class V2:
        """
        this class provides methods to interact with the fine-tuning V2 API.
        """

        @classmethod
        def base_api_route(cls) -> str:
            """
            base api url route for fine-tuning V2.

            Returns:
                str: base api url route
            """
            return Consts.FineTuneV2BaseRouteAPI

        @classmethod
        @console_api_request
        def create_job(
            cls,
            name: str,
            model: str,
            train_mode: Union[str, console_consts.TrainMode],
            description: Optional[str] = None,
            **kwargs: Any,
        ) -> QfRequest:
            """
            create a fine-tuning job.

            This function create a fine-tuning job. job may be associated with
            many tasks.

            Parameters:
            name (str):
                The name of job.
            model (str):
                The identifier of the fine-tuning job to be stopped.
                e.g. "ERNIE-Speed"
            train_mode (Union[str, console_consts.TrainMode]):
                The train mode of the fine-tuning job, including "SFT" and
                "PostPreTrain" and so on.
            description (Optional[str]):
                The description of the fine-tuning job.
            kwargs:
                Additional keyword arguments that can be passed to customize the
                request.

            Note:
            The `@console_api_request` decorator is applied to this method, enabling
            it to send the generated QfRequest and return a QfResponse to the user.

            API Doc: https://cloud.baidu.com/doc/WENXINWORKSHOP/s/2lnlebz15
            """
            req = QfRequest(
                method="POST",
                url=cls.base_api_route(),
                query=_get_console_v2_query(Consts.FineTuneCreateJobAction),
            )
            req.json_body = {**kwargs, "name": name, "model": model}
            if isinstance(train_mode, console_consts.TrainMode):
                req.json_body["trainMode"] = train_mode.value
            elif isinstance(train_mode, str):
                req.json_body["trainMode"] = train_mode
            else:
                raise TypeError(
                    "train_mode must be a string or TrainMode, but got"
                    f" {type(train_mode)}"
                )
            if description is not None:
                req.json_body["description"] = description
            return req

        @classmethod
        @console_api_request
        def create_task(
            cls,
            job_id: str,
            params_scale: Union[str, console_consts.TrainParameterScale],
            hyper_params: Dict[str, Any],
            dataset_config: Dict[str, Any],
            incrementTaskId: Optional[str] = None,
            **kwargs: Any,
        ) -> QfRequest:
            """
            create a fine-tuning task.

            This function create a fine-tuning task associated with a
            specific job.

            Parameters:
            name (str):
                The name of job.
            model (str):
                The identifier of the fine-tuning job to be stopped.
                e.g. "ERNIE-Speed"
            train_mode (Union[str, console_consts.TrainMode]):
                The train mode of the fine-tuning job, including "SFT",
                "PostPreTrain" and so on.
            description (Optional[str]):
                The description of the fine-tuning job.
            kwargs:
                Additional keyword arguments that can be passed to customize
                the request.

            Note:
            The `@console_api_request` decorator is applied to this method, enabling
            it to send the generated QfRequest and return a QfResponse to the user.
            """
            req = QfRequest(
                method="POST",
                url=cls.base_api_route(),
                query=_get_console_v2_query(Consts.FineTuneCreateTaskAction),
            )
            req.json_body = {
                **kwargs,
                "jobId": job_id,
                "parameterScale": (
                    params_scale.value
                    if isinstance(params_scale, console_consts.TrainParameterScale)
                    else params_scale
                ),
                "hyperParameterConfig": hyper_params,
                "datasetConfig": dataset_config,
            }
            if incrementTaskId is not None:
                req.json_body["incrementTaskId"] = incrementTaskId
            return req

        @classmethod
        @console_api_request
        def job_list(
            cls,
            train_model: Optional[Union[str, console_consts.TrainMode]] = None,
            marker: Optional[str] = None,
            max_keys: Optional[int] = None,
            page_reverse: Optional[bool] = None,
            **kwargs: Any,
        ) -> QfRequest:
            """
            get fine-tune job list .

            Parameters:
            train_model: Optional[Union[str, console_consts.TrainMode]] = None,
                "SFT" or "PostPretrain"
            marker: Optional[str] = None,
                job_id, the marker of the first page.
            max_keys: Optional[int] = None,
                max keys of the page.
            page_reverse: Optional[bool] = None,
                page reverse or not.
            kwargs:
                Additional keyword arguments that can be passed to customize
                the request.

            Note:
            The `@console_api_request` decorator is applied to this method, enabling
            it to send the generated QfRequest and return a QfResponse to the user.
            """
            req = QfRequest(
                method="POST",
                url=cls.base_api_route(),
                query=_get_console_v2_query(Consts.FineTuneJobListAction),
            )
            req.json_body = {
                k: v
                for k, v in {
                    **kwargs,
                    "trainModel": (
                        train_model.value
                        if isinstance(train_model, console_consts.TrainMode)
                        else train_model
                    ),
                    "maker": marker,
                    "maxKeys": max_keys,
                    "pageReverse": page_reverse,
                }.items()
                if v is not None
            }
            return req

        @classmethod
        @console_api_request
        def task_list(
            cls,
            job_id: str,
            marker: Optional[str] = None,
            max_keys: Optional[int] = None,
            page_reverse: Optional[bool] = None,
            **kwargs: Any,
        ) -> QfRequest:
            """
            get fine-tune task list .

            Parameters:
            job: str
                job_id of tasks.
            marker: Optional[str] = None,
                job_id, the marker of the first page.
            max_keys: Optional[int] = None,
                max keys of the page.
            page_reverse: Optional[bool] = None,
                page reverse or not.
            kwargs:
                Additional keyword arguments that can be passed to customize
                the request.

            Note:
            The `@console_api_request` decorator is applied to this method, enabling
            it to send the generated QfRequest and return a QfResponse to the user.
            """
            req = QfRequest(
                method="POST",
                url=cls.base_api_route(),
                query=_get_console_v2_query(Consts.FineTuneTaskListAction),
            )
            req.json_body = {
                k: v
                for k, v in {
                    **kwargs,
                    "jobId": job_id,
                    "maker": marker,
                    "maxKeys": max_keys,
                    "pageReverse": page_reverse,
                }.items()
                if v is not None
            }
            return req

        @classmethod
        @console_api_request
        def task_detail(
            cls,
            task_id: str,
            **kwargs: Any,
        ) -> QfRequest:
            """
            get the fine-tune task detail

            Parameters:
            task_id: str
                task_id of the task.
            kwargs:
                Additional keyword arguments that can be passed to customize
                the request.

            Note:
            The `@console_api_request` decorator is applied to this method, enabling
            it to send the generated QfRequest and return a QfResponse to the user.
            """
            req = QfRequest(
                method="POST",
                url=cls.base_api_route(),
                query=_get_console_v2_query(Consts.FineTuneTaskDetailAction),
            )
            req.json_body = {
                **kwargs,
                "taskId": task_id,
            }
            return req

        @classmethod
        @console_api_request
        def stop_task(
            cls,
            task_id: str,
            **kwargs: Any,
        ) -> QfRequest:
            """
            stop the fine-tune task

            Parameters:
            task_id: str
                task_id of the task.
            kwargs:
                Additional keyword arguments that can be passed to customize
                the request.

            Note:
            The `@console_api_request` decorator is applied to this method, enabling
            it to send the generated QfRequest and return a QfResponse to the user.
            """
            req = QfRequest(
                method="POST",
                url=cls.base_api_route(),
                query=_get_console_v2_query(Consts.FineTuneStopTaskAction),
            )
            req.json_body = {
                **kwargs,
                "taskId": task_id,
            }
            return req

        @classmethod
        @console_api_request
        def supported_models(cls, **kwargs: Any) -> QfRequest:
            """
            get the supported models and training params for
            fine-tuning

            Parameters:
            kwargs:
                Additional keyword arguments that can be passed to customize
                the request.

            Note:
            The `@console_api_request` decorator is applied to this method, enabling
            it to send the generated QfRequest and return a QfResponse to the user.
            """
            req = QfRequest(
                method="POST",
                url=cls.base_api_route(),
                query=_get_console_v2_query(Consts.FineTuneSupportedModelsAction),
            )
            return req
