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
from datetime import datetime
from typing import Any, Dict, Iterator, Optional, Union

from qianfan import resources as api
from qianfan.common import Prompt
from qianfan.common.runnable.base import ExecuteSerializable
from qianfan.config import get_config
from qianfan.dataset import Dataset
from qianfan.errors import InternalError, InvalidArgumentError
from qianfan.model.configs import DeployConfig
from qianfan.model.consts import ServiceType
from qianfan.resources import (
    ChatCompletion,
    Completion,
    Embedding,
    QfResponse,
    Text2Image,
)
from qianfan.resources.console import consts as console_const
from qianfan.resources.console.model import Model as ResourceModel
from qianfan.utils import log_debug, log_error, log_info, log_warn
from qianfan.utils.utils import generate_letter_num_random_id


class Model(
    ExecuteSerializable[Dict, Union[QfResponse, Iterator[QfResponse]]],
):
    set_id: Optional[str]
    """remote model set id"""
    id: Optional[str]
    """remote model version id"""
    name: Optional[str] = None
    """model name"""
    service: Optional["Service"] = None
    """model service"""
    task_id: Optional[str]
    """train tkas id"""
    job_id: Optional[str]
    """train job id"""
    step: Optional[int] = None
    """checkpoint step"""

    def __init__(
        self,
        set_id: Optional[str] = None,
        id: Optional[str] = None,
        task_id: Optional[str] = None,
        job_id: Optional[str] = None,
        name: Optional[str] = None,
        **kwargs: Any,
    ):
        """
        Class for model in qianfan, which is deployable by using deploy() to
        get a custom model service.

        Parameters:
            set_id (Optional[str], optional):
                qianfan model remote set id. Defaults to None.
            id (Optional[str], optional):
                model id. Defaults to None.
            task_id (Optional[int], optional):
                model train task id. Defaults to None.
            job_id (Optional[int], optional):
                model train job id. Defaults to None.
            auto_complete (Optional[bool], optional):
                if call auto_complete() to complete model info. Defaults to None.
        """
        self.set_id = set_id
        self.id = id
        self.task_id = task_id
        self.job_id = job_id
        self.name = name
        if id is None or set_id is None:
            self.auto_complete_info()

    def exec(
        self, input: Optional[Dict] = None, **kwargs: Dict
    ) -> Union[QfResponse, Iterator[QfResponse]]:
        """
        model execution, for different model service type, please input
        a dict with different keys.
        Concretely, take
            `input={"messages": [{"role": "user",
                    "content": "hello world"}]}`
        as input, when the model is a chat io Model.

        Parameters:
            input (Optional[Dict], optional):
                input data . Defaults to None.

        Raises:
            InternalError: model with no service deployed is unable to call exec

        Returns:
            Union[QfResponse, Iterator[QfResponse]]:
                output data
        """
        if self.service is None:
            raise InternalError(
                "model not deployed, call `model_deploy()` to instantiate a service"
            )
        return self.service.exec(input, **kwargs)

    def deploy(self, deploy_config: DeployConfig, **kwargs: Any) -> "Service":
        """
        model deploy

        Parameters:
            deploy_config (DeployConfig):
                model service deploy config

        Returns:
            Service: model service instance
        """
        if self.service is None:
            self.service = model_deploy(self, deploy_config, **kwargs)
            return self.service
        log_info("model service already existed")
        return self.service

    def auto_complete_info(self, **kwargs: Any) -> None:
        """
        auto complete Model object's info.
        This may override the input model id version id.

        Parameters:
            **kwargs (Any):
                arbitrary arguments
        """
        if self.id:
            model_detail_resp = ResourceModel.detail(model_version_id=self.id, **kwargs)
            self.set_id = model_detail_resp["result"].get("modelIdStr")
        elif self.set_id:
            list_resp = ResourceModel.V2.describe_model_set(
                model_set_id=self.set_id, **kwargs
            )
            if len(list_resp["result"]["modelIds"]) == 0:
                raise InvalidArgumentError(
                    "not model version matched, please train and publish first"
                )
            log_info("model publish get the first version in model list as default")
            self.id = list_resp["result"]["modelIds"][0]
            if self.id is None:
                raise InvalidArgumentError("model version id not found")

    def publish(self, name: str = "", **kwargs: Any) -> "Model":
        """
        model publish, before deploying a model, it should be published.

        Parameters:
            name str:
                model name. Defaults to "m_{task_id}{job_id}".
        """
        if self.id:
            # already released
            model_detail_resp = ResourceModel.detail(model_version_id=self.id, **kwargs)
            self.set_id = model_detail_resp["result"]["modelIdStr"]
            self.task_id = model_detail_resp["result"]["sourceExtra"][
                "trainSourceExtra"
            ]["taskId"]
            self.job_id = model_detail_resp["result"]["sourceExtra"][
                "trainSourceExtra"
            ]["runId"]
            log_info(f"check model {self.set_id}/{self.id} published...")
            if model_detail_resp["result"]["state"] != console_const.ModelState.Ready:
                self._wait_for_publish(**kwargs)
        elif self.set_id:
            list_resp = ResourceModel.V2.describe_model_set(
                model_set_id=self.set_id, **kwargs
            )
            if len(list_resp["result"]["modelIds"]) == 0:
                raise InvalidArgumentError(
                    "not model version matched, please train and publish first"
                )
            log_info("model publish get the first version in model list as default")
            self.id = list_resp["result"]["modelIds"][0]
            if self.id is None:
                raise InvalidArgumentError("model version id not found")
            model_detail_resp = ResourceModel.detail(model_version_id=self.id, **kwargs)
            self.task_id = model_detail_resp["result"]["sourceExtra"][
                "trainSourceExtra"
            ]["taskId"]
            self.job_id = model_detail_resp["result"]["sourceExtra"][
                "trainSourceExtra"
            ]["runId"]
            if model_detail_resp["result"]["state"] != console_const.ModelState.Ready:
                self._wait_for_publish(**kwargs)
        # 检查是否训练完成
        log_info(
            f"check train job: {self.task_id}/{self.job_id} status before publishing"
            " model"
        )
        if self.task_id is None or self.job_id is None:
            raise InvalidArgumentError("task id or job id not found")
        # 判断训练任务已经训练完成：
        while True:
            job_status_resp = api.FineTune.V2.task_detail(
                task_id=self.task_id,
                **kwargs,
            )
            job_status = job_status_resp["result"]["runStatus"]
            log_info(f"model publishing keep polling, current status {job_status}")
            if job_status == console_const.TrainStatus.Running:
                time.sleep(get_config().TRAIN_STATUS_POLLING_INTERVAL)
                continue
            elif job_status == console_const.TrainStatus.Finish:
                break
            else:
                raise InvalidArgumentError("invalid train task job to publish model")
        # 发布模型
        self.model_name = (
            name if name != "" else f"m_{generate_letter_num_random_id(12)}"
        )
        model_version_meta: Dict[str, Any] = {
            "taskId": self.job_id,
            "iterationId": self.task_id,
        }
        if self.step:
            model_version_meta["step"] = self.step
        model_publish_resp = ResourceModel.publish(
            is_new=True,
            model_name=self.model_name,
            version_meta=model_version_meta,
            **kwargs,
        )
        self.set_id = model_publish_resp["result"]["modelIDStr"]

        if self.set_id is None:
            raise InvalidArgumentError("model id not found")
        # 获取模型版本信息：
        model_list_resp = ResourceModel.V2.describe_model_set(
            model_set_id=self.set_id, **kwargs
        )
        model_version_list = model_list_resp["result"]["modelIds"]
        if model_version_list is None or len(model_version_list) == 0:
            raise InvalidArgumentError("not model version matched")
        self.id = model_version_list[0]

        if self.id is None:
            raise InvalidArgumentError("model version id not found")
        log_info(
            f"publishing train task: {self.job_id}/{self.task_id} to model:"
            f" {self.set_id}/{self.id}"
        )
        self._wait_for_publish(**kwargs)
        log_info(f"publish successfully to model: {self.set_id}/{self.id}")
        return self

    def _wait_for_publish(self, **kwargs: Any) -> None:
        """
        call a polling loop to wait until the model is published.

        Raises:
            InternalError: _description_
        """
        # 获取模型版本详情
        if self.id is None:
            raise InvalidArgumentError("model version id not found")
        while True:
            model_detail_info = ResourceModel.detail(model_version_id=self.id, **kwargs)
            model_version_state = model_detail_info["result"]["state"]
            log_debug(f"check model publish status: {model_version_state}")
            if model_version_state == console_const.ModelState.Ready:
                log_info(f"model {self.set_id}/{self.id} published successfully")
                break
            elif model_version_state == console_const.ModelState.Fail:
                raise InternalError(
                    "model published failed, check error msg and retry."
                    f" {model_detail_info}"
                )
            time.sleep(get_config().MODEL_PUBLISH_STATUS_POLLING_INTERVAL)

    def dumps(self) -> Optional[bytes]:
        """
        Serialize the model to bytes.

        Returns:
            Optional[bytes]:
                bytes of this model
        """
        return pickle.dumps(self)

    def loads(self, data: bytes) -> Any:
        """
        load model instance from bytes

        Parameters:
            data (bytes):
                bytes of this model

        Returns:
            Any: model instance
        """
        return pickle.loads(data)

    def batch_inference(self, dataset: Dataset, **kwargs: Any) -> Dataset:
        """
        create batch run using specific dataset on qianfan
        by evaluation ability of platform

        Parameters:
            dataset (Dataset):
                A dataset instance which indicates a dataset on qianfan platform
            **kwargs (Any):
                Arbitrary keyword arguments

        Returns:
            Dataset: batch result contained in dataset
        """

        return dataset.test_using_llm(self.id, **kwargs)

    def compress(
        self,
        strategy: Union[console_const.ModelCompStrategy, str],
        weight: Optional[Union[console_const.ModelQuantizationWeight, str]] = None,
    ) -> "Model":
        """
        try compress model and return a new 'Model' or raise an exception

        Parameters:
            strategy Union[ModelCompStrategy, str]:
                a compression strategy, please refer to ModelCompStrategy
            weight Optional[Union[ModelQuantizationWeight, str]] = None:
                a weight of quantization, only supported when strategy is
                ModelCompStrategy.Quantization

        Returns:
            Model: new compressed model

        """
        self.auto_complete_info()
        assert self.id is not None
        assert self.set_id is not None
        model_detail_resp = ResourceModel.V2.describe_model(model_id=self.id)
        if not model_detail_resp["result"].get("isSupportModelComp"):
            log_error(f"model {self.id} is not supported to compress")
            raise InvalidArgumentError(f"model {self.id} is not supported to compress")
        strategy = console_const.ModelCompStrategy(strategy)
        config = {"strategy": strategy.value}
        if strategy == console_const.ModelCompStrategy.Quantization:
            if weight is None:
                log_error("weight parameter required when quantization compression.")
                raise InvalidArgumentError(
                    "weight parameter required when quantization compression."
                )
            else:
                config["weight"] = console_const.ModelQuantizationWeight(weight).value
        model_comp_task_resp = ResourceModel.V2.create_model_comp_task(
            name=f"mco_{generate_letter_num_random_id(12)}",
            source_model_id=self.id,
            config=config,
            model_set_id=self.set_id,
            description=f"mcomp_{self.id}_{strategy.value}_{weight}",
        )
        model_comp_task_id = model_comp_task_resp["result"]
        log_info(f"started compressing task: {model_comp_task_id}")
        while True:
            time.sleep(15)
            comp_task_detail_resp = ResourceModel.V2.describe_model_comp_task(
                model_comp_task_id
            )
            if comp_task_detail_resp["result"]["status"] in [
                console_const.ModelCompTaskStatus.Running.value,
                console_const.ModelCompTaskStatus.Creating.value,
            ]:
                log_info(f"model compress running with task: {model_comp_task_id}")
            elif (
                comp_task_detail_resp["result"]["status"]
                == console_const.ModelCompTaskStatus.Succeeded.value
            ):
                new_model_id = comp_task_detail_resp["result"].get("modelId")
                log_info(
                    f"compress task {model_comp_task_id} run with status"
                    f" {comp_task_detail_resp['result']['status']}"
                    f" new model_id: {new_model_id}"
                )
                new_model = Model(id=new_model_id)
                new_model.auto_complete_info()
                return new_model
            else:
                log_error(
                    f"compress task {model_comp_task_id} run with status"
                    f" {comp_task_detail_resp['result']['status']}, please check it"
                    " manually"
                )
                raise InternalError(
                    f"compress task {model_comp_task_id} run with status"
                    f" {comp_task_detail_resp['result']['status']}, failed reason:"
                    f" {comp_task_detail_resp['result'].get('failedReason')}"
                )


class Service(ExecuteSerializable[Dict, Union[QfResponse, Iterator[QfResponse]]]):
    id: Optional[str]
    """remote service id"""
    model: Optional[Model]
    """service model instance"""
    deploy_config: Optional[DeployConfig]
    """service deploy config"""
    endpoint: Optional[str]
    """service endpoint to call"""
    service_type: Optional[ServiceType]
    """service type, for user use service as a execution must specify"""

    # service type may get from model ioModel

    def __init__(
        self,
        id: Optional[str] = None,
        endpoint: Optional[str] = None,
        model: Optional[Union[Model, str]] = None,
        deploy_config: Optional[DeployConfig] = None,
        service_type: Optional[ServiceType] = None,
    ) -> None:
        """
        Class for model in qianfan, which is deployable by using deploy() to
        get a custom model service.

        Parameters:
            id (Optional[Union[int, str]], optional):
                qianfan service id. Defaults to None.
            endpoint (Optional[str], optional):
                qianfan service endpoint. Defaults to None.
            model (Optional[Model], optional):
                service's corresponding model. Defaults to None.
            deploy_config (Optional[DeployConfig], optional):
                service deploy config. Defaults to None.
            service_type (Optional[ServiceType], optional):
                service type, for user use service as a execution must specify,
                Defaults to None.
        """
        self.id = id
        self.service_type = service_type
        if self.service_type is None:
            log_warn("service type should be specified before exec")
        if endpoint is not None:
            self.model = None
            self.endpoint = endpoint
        elif isinstance(model, str):
            self.model = Model(name=model)
            self.endpoint = None
        elif isinstance(model, Model):
            # need to deploy
            self.model = model
            self.endpoint = None
        else:
            raise InvalidArgumentError("invalid model service")
        self.deploy_config = deploy_config

    @property
    def status(self) -> str:
        """
        get the service status

        Raises:
            InternalError: id not found

        Returns:
            console_const.ServiceStatus
        """
        if self.id is None:
            return ""
        elif isinstance(self.id, str):
            resp = api.Service.V2.service_detail(
                service_id=self.id,
                retry_count=get_config().TRAINER_STATUS_POLLING_RETRY_TIMES,
                backoff_factor=get_config().TRAINER_STATUS_POLLING_BACKOFF_FACTOR,
            )
            return resp["result"]["runStatus"]
        else:
            raise InternalError("id type not supported")

    def exec(
        self, input: Optional[Dict] = None, **kwargs: Dict
    ) -> Union[QfResponse, Iterator[QfResponse]]:
        """
        exec

        Parameters:
            input (Optional[Union[str, List[str], List[dict]]], optional):
                input of execution of service. Defaults to None.
            **kwargs: additional args Dict
        Raises:
            InternalError: unsupported service type

        Returns:
            Union[str, List[str], List[dict]]:
                output
        """
        if input is None:
            raise InvalidArgumentError("input is none")
        return self.get_res().do(**{**input, **kwargs})

    def get_res(self) -> Union[ChatCompletion, Completion, Embedding, Text2Image]:
        """
        convert to the specific model resources. e.g.
        `ChatCompletion`, `Completion`, `Embeddings`,
        `Text2Image`

        Returns:
            Union[ChatCompletion, Completion, Embedding, Text2Image]:
                resource object
        """
        if self.endpoint is not None and self.service_type is None:
            raise InvalidArgumentError(
                "service type must be specified when endpoint passed in"
            )
        svc_status = self.status
        if svc_status not in [
            console_const.ServiceStatus.Done,
            console_const.ServiceStatus.Serving,
        ]:
            log_warn("service status unknown, service could be unavailable.")
        if self.service_type == ServiceType.Chat:
            return ChatCompletion(
                endpoint=self.endpoint,
            )
        elif self.service_type == ServiceType.Completion:
            return Completion(
                endpoint=self.endpoint,
            )
        elif self.service_type == ServiceType.Embedding:
            return Embedding(
                endpoint=self.endpoint,
            )
        elif self.service_type == ServiceType.Text2Image:
            return Text2Image(
                endpoint=self.endpoint,
            )
        else:
            raise InvalidArgumentError(f"unsupported service type {self.service_type}")

    def metrics(
        self, start_time: datetime, end_time: datetime, **kwargs: Any
    ) -> Dict[str, Any]:
        """
        return the service metrics in the specified time range

        Args:
            start_time (datetime): start datetime
            end_time (datetime): end datetime

        Returns:
            Dict[str, Any]: _description_
        """
        assert self.id is not None
        return api.Service.V2.service_metric(
            start_time=start_time, end_time=end_time, service_id=[self.id]
        )["result"]["serviceList"][0]

    def deploy(self, **kwargs: Any) -> "Service":
        if self.model is None:
            raise InvalidArgumentError("model not found")
        model = self.model
        if model.set_id is None or model.id is None:
            raise InvalidArgumentError("model set id | model id not found")
        if self.deploy_config is None:
            raise InvalidArgumentError("deploy config not found")
        log_info(f"ready to deploy service with model {model.set_id}/{model.id}")
        model.auto_complete_info()
        res_config: Dict[str, Any] = {
            "type": self.deploy_config.resource_type,
            "replicasCount": self.deploy_config.replicas,
        }
        if self.deploy_config.qps is not None:
            res_config["qps"] = self.deploy_config.qps
        svc_publish_resp = api.Service.V2.create_service(
            model_set_id=model.set_id,
            model_id=model.id,
            name=self.deploy_config.name or f"svc{model.set_id}_{model.id}",
            url_suffix=self.deploy_config.endpoint_suffix
            or f"svc{model.set_id}_{model.id}",
            resource_config=res_config,
            billing={
                "paymentTiming": "Prepaid",
                "reservation": {
                    "reservationTimeUnit": (
                        "Month" if self.deploy_config.months else "Hour"
                    ),
                    "reservationLength": (
                        self.deploy_config.months or self.deploy_config.hours
                    ),
                },
            },
            **kwargs,
        )

        self.id = svc_publish_resp["result"]["serviceId"]
        if self.id is None:
            log_error("create service error", svc_publish_resp)
            raise InternalError("service id not found")
        # 资源付费完成后，serviceStatus会变成Deploying，查看模型服务状态
        while True:
            resp = api.Service.V2.service_detail(service_id=self.id, **kwargs)
            svc_status = resp["result"]["runStatus"]

            if svc_status in [
                console_const.ServiceStatus.Deploying.value,
                console_const.ServiceStatus.New.value,
            ]:
                # purchase_resp = api.Charge.purchase_service_resource(
                #     service_id = self.id,
                #     billing={},
                #     replicas=DeployConfig.replicas,
                # )
                # while True:
                #     inst_info_resp = api.Charge.get_service_resource_instance_info(
                #         service_id = self.id,
                #         instance_id = purchase_resp["result"]["instanceId"]
                #     )
                log_debug(f"service {self.id} status: {svc_status}")
            elif svc_status == console_const.ServiceStatus.Serving:
                sft_model_endpoint = resp["result"]["url"].split("/")[-1]
                log_info(
                    f"service {self.id} has been deployed in `{sft_model_endpoint}` "
                )
                break
            else:
                log_error(f"service {self.id} has been ended in {svc_status}")
                break
            time.sleep(get_config().DEPLOY_STATUS_POLLING_INTERVAL)

        self.endpoint = sft_model_endpoint
        return self

    def dumps(self) -> Optional[bytes]:
        """
        serialize the model instance to bytes

        Returns:
            Optional[bytes]:
                bytes of the model instance
        """
        return pickle.dumps(self)

    def loads(self, data: bytes) -> Any:
        """
        load service instance from bytes

        Parameters:
            data (bytes):
                bytes of model instance

        Returns:
            Any: model instance
        """
        return pickle.loads(data)

    def batch_inference(
        self,
        dataset: Dataset,
        prompt_template: Optional[Prompt] = None,
        system_prompt: Optional[str] = None,
        **kwargs: Any,
    ) -> Dataset:
        """
        create batch run using specific dataset on qianfan

        Args:
            dataset (Dataset):
                A dataset instance which indicates a dataset on qianfan platform
            prompt_template (Optional[Prompt]):
                Optional Prompt used as input of llm, default to None.
                Only used when your Service is a Completion service
            system_prompt (Optional[str]):
                Optional system text for input using, default to None.
                Only used when your Service is a ChatCompletion service
            **kwargs (Any):
                Arbitrary keyword arguments

        Returns:
            Dataset: batch result contained in dataset
        """

        return dataset.test_using_llm(
            service_model=self.model.name if self.model else None,
            service_endpoint=self.endpoint,
            is_chat_service=isinstance(self.get_res(), ChatCompletion),
            prompt_template=prompt_template,
            system_prompt=system_prompt,
        )


def model_deploy(model: Model, deploy_config: DeployConfig, **kwargs: Any) -> Service:
    """
    model deployment implement, a polling loop will be called after
    deploy task created.

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
    svc.deploy(**kwargs)
    return svc
