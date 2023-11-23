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
import pickle
import time
from typing import Any, Dict, Iterator, Optional, Union

from qianfan import resources as api
from qianfan.config import get_config
from qianfan.errors import InternalError, InvalidArgumentError
from qianfan.resources import ChatCompletion, Completion, QfResponse, Text2Image
from qianfan.resources.console import consts as console_const
from qianfan.trainer.base import ExecuteSerializable
from qianfan.trainer.configs import DeployConfig
from qianfan.trainer.consts import ServiceType


class Model(
    ExecuteSerializable[Dict, Union[QfResponse, Iterator[QfResponse]]],
):
    id: Optional[int]
    """remote model id"""
    version_id: Optional[int]
    """remote model version id"""
    name: str
    """model name"""
    service: Optional["Service"] = None
    """model service"""
    task_id: Optional[int]
    """train tkas id"""
    job_id: Optional[int]
    """train job id"""

    def __init__(
        self,
        id: Optional[int] = None,
        version_id: Optional[int] = None,
        task_id: Optional[int] = None,
        job_id: Optional[int] = None,
    ):
        """
        Class for model in qianfan, which is deployable by using deploy() to
        get a custom model service.

        Parameters:
            id (Optional[int], optional):
                qianfan model remote id. Defaults to None.
            version_id (Optional[int], optional):
                model version id. Defaults to None.
            task_id (Optional[int], optional):
                model train task id. Defaults to None.
            job_id (Optional[int], optional):
                model train job id. Defaults to None.
        """
        self.id = id
        self.version_id = version_id
        self.task_id = task_id
        self.job_id = job_id

    def exec(
        self, input: Optional[Dict] = None, **kwargs: Dict
    ) -> Union[QfResponse, Iterator[QfResponse]]:
        if self.service is None:
            raise InternalError(
                "model not deployed, call `model_deploy()` to instantiate a service"
            )
        return self.service.exec(input, **kwargs)

    def deploy(self, deploy_config: DeployConfig) -> "Service":
        self.service = model_deploy(self, deploy_config)

        return self.service

    def publish(self, name: str = "") -> "Model":
        # 发布模型
        self.model_name = name if name != "" else f"m_{self.task_id}{self.job_id}"
        model_publish_resp = api.Model.publish(
            is_new=True,
            model_name=self.model_name,
            version_meta={"taskId": self.task_id, "iterationId": self.job_id},
        )

        self.id = model_publish_resp["result"]["modelId"]
        if self.task_id is None or self.job_id is None:
            raise InvalidArgumentError("task id or job id not found")
        while True:
            job_status_resp = api.FineTune.get_job(
                task_id=self.task_id, job_id=self.job_id
            )
            job_status = job_status_resp["result"]["trainStatus"]
            if job_status != console_const.TrainStatus.Running:
                break
            time.sleep(get_config().TRAIN_STATUS_POLLING_INTERVAL)

        if self.id is None:
            raise InvalidArgumentError("model id not found")
        # 获取模型版本信息：
        model_list_resp = api.Model.list(model_id=self.id)
        model_version_list = model_list_resp["result"]["modelVersionList"]
        if model_version_list is None or len(model_version_list) == 0:
            raise InvalidArgumentError("not model version matched")
        self.version_id = model_version_list[0]["modelVersionId"]

        if self.version_id is None:
            raise InvalidArgumentError("model version id not found")
        # 获取模型版本详情
        while True:
            model_detail_info = api.Model.detail(model_version_id=self.version_id)
            model_version_state = model_detail_info["result"]["state"]
            if model_version_state == console_const.ModelState.Ready:
                break
            elif model_version_state == console_const.ModelState.Fail:
                raise InternalError("model published failed")
            time.sleep(get_config().MODEL_PUBLISH_STATUS_POLLING_INTERVAL)
        return self

    def dumps(self) -> Optional[bytes]:
        return pickle.dumps(self)

    def loads(self, data: bytes) -> Any:
        return pickle.loads(data)


class Service(ExecuteSerializable[Dict, Union[QfResponse, Iterator[QfResponse]]]):
    id: Optional[int]
    model: Optional[Model]
    deploy_config: Optional[DeployConfig]
    endpoint: str
    service_type: Optional[ServiceType]

    def __init__(
        self,
        id: Optional[int] = None,
        model: Optional[Model] = None,
        deploy_config: Optional[DeployConfig] = None,
        service_type: Optional[ServiceType] = None,
    ) -> None:
        """
        Class for model in qianfan, which is deployable by using deploy() to
        get a custom model service.

        Parameters:
            id (Optional[int], optional):
                qianfan service id. Defaults to None.
            model (Optional[Model], optional):
                service's corresponding model. Defaults to None.
            deploy_config (Optional[DeployConfig], optional):
                service deploy config. Defaults to None.
            service_type (Optional[ServiceType], optional):
                service type, for user use service as a execution must specify,
                Defaults to None.
        """
        self.id = id
        self.model = model
        self.deploy_config = deploy_config
        self.service_type = service_type

    @property
    def status(self) -> console_const.ServiceStatus:
        if self.id is None:
            raise InternalError("service id not found")
        resp = api.Service.get(id=self.id)
        return resp["result"]["serviceStatus"]

    def exec(
        self, input: Optional[Dict] = None, **kwargs: Dict
    ) -> Union[QfResponse, Iterator[QfResponse]]:
        """
        exec

        Args:
            input (Optional[Union[str, List[str], List[dict]]], optional):
                input of execution of service. Defaults to None.
            **kwargs: additional args Dict
        Raises:
            InternalError: _description_

        Returns:
            Union[str, List[str], List[dict]]: _description_
        """
        if input is None:
            raise InvalidArgumentError("input is none")
        if self.status != console_const.ServiceStatus.Done:
            raise InternalError("service is not ready")
        if self.service_type == ServiceType.Chat:
            return ChatCompletion().do(endpoint=self.endpoint, **input)
        elif self.service_type == ServiceType.Completion:
            return Completion().do(endpoint=self.endpoint, **input)
        elif self.service_type == ServiceType.Text2Image:
            return Text2Image().do(endpoint=self.endpoint, **input)
        else:
            raise InvalidArgumentError(f"unsupported service type {self.service_type}")

    def dumps(self) -> Optional[bytes]:
        return pickle.dumps(self)

    def loads(self, data: bytes) -> Any:
        return pickle.loads(data)


def model_deploy(model: Model, deploy_config: DeployConfig) -> Service:
    """
    model deployment implement, a polling loop will be called after
    deploy task created

    Parameters:
        model (Model):
            model to deploy
        deploy_config (DeployConfig):
            service deploy config, mainly including replicas
            and pool type.

    Returns:
        Service: deployed service with endpoint to call
    """
    svc = Service(
        model=model,
        deploy_config=deploy_config,
        service_type=deploy_config.service_type,
    )
    if model.id is None or model.version_id is None:
        raise InvalidArgumentError("model id | model version id not found")
    svc_publish_resp = api.Service.create(
        model_id=model.id,
        model_version_id=model.version_id,
        iteration_id=model.version_id,
        name=f"svc{model.id}{model.version_id}",
        uri=f"ep{model.id}{model.version_id}",
        replicas=deploy_config.replicas,
        pool_type=deploy_config.pool_type,
    )

    svc.id = svc_publish_resp["result"]["serviceId"]
    if svc.id is None:
        raise InternalError("service id not found")
    # 资源付费完成后，serviceStatus会变成Deploying，查看模型服务状态
    while True:
        resp = api.Service.get(id=svc.id)
        svc_status = resp["result"]["serviceStatus"]
        if svc_status != console_const.ServiceStatus.Deploying.value:
            sft_model_endpoint = resp["result"]["uri"]
            break
        time.sleep(get_config().DEPLOY_STATUS_POLLING_INTERVAL)

    svc.endpoint = sft_model_endpoint
    return svc
