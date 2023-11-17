import time
import uuid
from typing import Any, Dict, Optional, cast

from qianfan import resources as api
from qianfan.errors import InvalidArgumentError
from qianfan.resources.console import consts as console_const
from qianfan.trainer.base import (
    BaseAction,
    Event,
    EventHandler,
    Pipeline,
    Trainer,
    dispatch_event,
)
from qianfan.trainer.configs import DeployConfig, TrainConfig
from qianfan.trainer.consts import (
    ActionState,
    ModelTypeMapping,
    TrainMode,
)

DefaultTrainConfigMapping: Dict[str, TrainConfig] = {
    "ERNIE-Bot-turbo-0725": TrainConfig(
        epoch=1,
        batch_size=4,
        learning_rate=0.0002,
        max_seq_len=4096,
        peft_type="LoRA",
    ),
    "ERNIE-Bot-turbo-0516": TrainConfig(
        epoch=1,
        batch_size=4,
        learning_rate=0.0002,
        max_seq_len=4096,
        peft_type="LoRA",
    ),
    "ERNIE-Bot-turbo-0704": TrainConfig(
        epoch=1,
        batch_size=4,
        learning_rate=0.0002,
        max_seq_len=4096,
        peft_type="LoRA",
    ),
    "Llama-2-7b": TrainConfig(
        epoch=1,
        batch_size=4,
        learning_rate=0.0002,
        max_seq_len=4096,
        peft_type="LoRA",
    ),
    "Llama-2-13b": TrainConfig(
        epoch=1,
        batch_size=4,
        learning_rate=0.0002,
        max_seq_len=4096,
        peft_type="LoRA",
    ),
    "SQLCoder-7B": TrainConfig(
        epoch=1,
        batch_size=4,
        learning_rate=0.0002,
        max_seq_len=4096,
        peft_type="LoRA",
    ),
    "ChatGLM2-6B": TrainConfig(
        epoch=1,
        batch_size=4,
        learning_rate=0.0002,
        max_seq_len=4096,
        peft_type="LoRA",
    ),
    "Baichuan2-13B": TrainConfig(
        epoch=1,
        batch_size=4,
        learning_rate=0.0002,
        max_seq_len=4096,
        peft_type="LoRA",
    ),
    "BLOOMZ-7B": TrainConfig(
        epoch=1,
        batch_size=4,
        learning_rate=0.0002,
        max_seq_len=4096,
        peft_type="LoRA",
    ),
}


def get_default_train_config(model_type: str) -> TrainConfig:
    return DefaultTrainConfigMapping.get(
        model_type, DefaultTrainConfigMapping["ERNIE-Bot-turbo-0725"]
    )


def wrap_error_output(e: Exception) -> Dict[str, Any]:
    return {"error": e}


class TrainAction(
    BaseAction[Dict[str, Any], Dict[str, Any]],
):
    is_incr: bool = False

    def __init__(
        self,
        base_model_version: str,
        train_config: Optional[TrainConfig] = None,
        base_model: Optional[str] = None,
        model_type: str = "",
        task_id: Optional[int] = None,
        job_id: Optional[int] = None,
        train_mode: Optional[TrainMode] = None,
        **kwargs: Any
    ) -> None:
        super().__init__(**kwargs)
        self.base_model_version = base_model_version
        self.base_model = base_model
        self.model_type = ModelTypeMapping.get(model_type)
        self.train_config = (
            train_config
            if train_config is None
            else get_default_train_config(base_model_version)
        )
        self.task_id = task_id
        self.task_id = job_id
        self.train_mode = train_mode
    def exec(self, input: Dict[str, Any], **kwargs: Dict[str, Any]) -> Dict[str, Any]:
        # request for create model train task
        try:
            resp = api.FineTune.create_task(name=str(uuid.uuid4()))
            self.task_id = cast(int, resp["result"]["id"])
        except Exception as e:
            dispatch_event(
                self.event_dispatcher,
                Event(
                    self.id,
                    ActionState.Error,
                    "action_error: action[{}], msg:{}".format(self.id, e),
                ),
            )
            return wrap_error_output(e)

        train_sets = input.get("datasets")
        if train_sets is None or len(train_sets) == 0:
            dispatch_event(
                self.event_dispatcher,
                Event(
                    self.id,
                    ActionState.Error,
                    "action_error: action[{}], msg:{}".format(self.id, "no trainset"),
                ),
            )
            return wrap_error_output(ValueError("trainset rate must be set"))

        # request for model train job
        try:
            assert self.train_config is not None
            req_job = {
                "taskId": self.task_id,
                "baseTrainType": self.base_model,
                "trainType": self.model_type,
                "trainMode": self.train_mode,
                "peftType": self.train_config.peft_type,
                "trainConfig": {
                    "epoch": self.train_config.epoch,
                    "learningRate": self.train_config.learning_rate,
                    "batchSize": self.train_config.batch_size,
                    "maxSeqLen": self.train_config.max_seq_len,
                },
                "trainset": train_sets,
                "trainsetRate": self.train_config.trainsetRate,
            }
            create_job_resp = api.FineTune.create_job(req_job)
            self.job_id = cast(int, create_job_resp["result"]["id"])
        except Exception as e:
            dispatch_event(
                self.event_dispatcher,
                Event(
                    self.id,
                    ActionState.Error,
                    "action_error: action[{}], msg:{}".format(self.id, e),
                ),
            )
            return wrap_error_output(e)

        while True:
            try:
                job_status_resp = api.FineTune.get_job(
                    task_id=self.task_id, job_id=self.job_id
                )
                job_status = job_status_resp["result"]["trainStatus"]
            except Exception as e:
                dispatch_event(
                    self.event_dispatcher,
                    Event(
                        self.id,
                        ActionState.Error,
                        "action_error: action[{}], msg:{}".format(self.id, e),
                    ),
                )
                return wrap_error_output(e)
            if job_status != "RUNNING":
                break
            time.sleep(10)

        try:
            self.model_name="model_{}{}".format(self.task_id, self.job_id)
            model_publish_resp = api.Model.publish(
                is_new=True,
                model_name=self.model_name,
                version_meta={"taskId": self.task_id, "iterationId": self.job_id},
            )
            # 获取model_id and version
            self.model_id = model_publish_resp["result"]["modelId"]
            self.model_version = model_publish_resp["result"]["version"]

            while True:
                try:
                    job_status_resp = api.FineTune.get_job(
                        task_id=self.task_id, job_id=self.job_id
                    )
                    job_status = job_status_resp["result"]["trainStatus"]
                except Exception as e:
                    dispatch_event(
                        self.event_dispatcher,
                        Event(
                            self.id,
                            ActionState.Error,
                            "action_error: action[{}], msg:{}".format(self.id, e),
                        ),
                    )
                    return wrap_error_output(e)
                if job_status != console_const.TrainStatus.Running:
                    break
                time.sleep(10)

            # 获取模型版本信息：
            model_list_resp = api.Model.list(model_id=self.model_id)
            model_version_list = model_list_resp["result"]["modelVersionList"]
            if model_version_list is None or len(model_version_list) == 0:
                return wrap_error_output(ValueError("not model version matched"))
            self.model_version_id = model_version_list[0]["modelVersionId"]

            # 获取模型版本详情
            # 模型版本状态有三种：Creating, Ready, Failed
            while True:
                model_detail_info = api.Model.detail(
                    model_version_id=self.model_version_id
                )
                model_version_state = model_detail_info["result"]["state"]
                if model_version_state == console_const.ModelState.Ready:
                    break
                elif model_version_state == console_const.ModelState.Fail:
                    self.event_dispatcher,
                    Event(
                        self.id,
                        ActionState.Error,
                        "action_error: action[{}], msg:{}".format(self.id, "model publish failed"),
                    ),
                    return wrap_error_output(e)
                time.sleep(20)

        except Exception as e:
            dispatch_event(
                self.event_dispatcher,
                Event(
                    self.id,
                    ActionState.Error,
                    "action_error: action[{}], msg:{}".format(self.id, e),
                ),
            )
            return wrap_error_output(e)
        return {"model_id": self.model_id, "model_version_id": self.model_version_id}

    def resume(self, input: Dict[str, Any], **kwargs: Dict) -> None:
        return None


class DeployAction(BaseAction[Dict[str, Any], Dict[str, Any]]):
    deploy_config: Optional[DeployConfig]
    model_id: int
    model_version_id: Optional[str] = None

    def __init__(
        self, deploy_config: Optional[DeployConfig] = None, **kwargs: Dict[str, Any]
    ):
        super().__init__(kwargs=kwargs)
        self.deploy_config = deploy_config

    def exec(self, input: Dict[str, Any], **kwargs: Dict) -> Dict[str, Any]:
        if self.deploy_config is None:
            return input
        self.model_id = input.get("model_id", "")
        self.mdoel_version_id = input.get("model_version_id", "")
        if self.model_id == "" or self.mdoel_version_id == "":
            return {}
        task_name_id = str(uuid.uuid4()).replace("-", "")

        svc_publish_resp = api.Service.create(
            model_id=self.model_id,
            model_version_id=self.mdoel_version_id,
            iteration_id=self.model_version_id,
            name="task_{}".format(task_name_id),
            uri="ep{}".format(task_name_id),
            replicas=self.deploy_config.replicas,
            pool_type=self.deploy_config.pool_type,
        )

        self.svc_id = svc_publish_resp["result"]["serviceId"]

        # 资源付费完成后，serviceStatus会变成Deploying，查看模型服务状态
        while True:
            resp = api.Service.get(id=self.svc_id)
            svc_status = resp["result"]["serviceStatus"]
            if svc_status != console_const.ServiceStatus.Deploying.value:
                sft_model_endpoint = resp["result"]["uri"]
                break
            time.sleep(20)
        return {"service_id": self.svc_id, "model_endpoint": sft_model_endpoint}

    def resume(self, input: Dict[str, Any], **kwargs: Dict) -> None:
        return None


class LoadDataSetAction(BaseAction[Dict[str, Any], Dict[str, Any]]):
    dataset: Any

    def __init__(
        self,
        dataset: Any = None,
        event_handler: Optional[EventHandler] = None,
        **kwargs: Dict[str, Any]
    ) -> None:
        super().__init__(event_handler=event_handler)
        self.dataset = dataset

    def exec(self, input: Dict[str, Any], **kwargs: Dict) -> Dict[str, Any]:
        if isinstance(self.dataset, Dict):
            return self.dataset
        return input

    def resume(self, input: Dict[str, Any], **kwargs: Dict) -> None:
        return None


class LLMFinetune(Trainer):
    def __init__(
        self,
        model_version_type: str,
        dataset: Any,
        train_config: Optional[TrainConfig] = None,
        deploy_config: Optional[DeployConfig] = None,
        model_id: Optional[str] = None,
        model_version_id: Optional[str] = None,
        event_handler: Optional[EventHandler] = None,
        base_model: Optional[str] = None,
        **kwargs: Any
    ) -> None:
        if model_version_id is not None and model_id is not None:
            # incr train
            pass

        if base_model is None and ModelTypeMapping.get(model_version_type) is not None:
            base_model = ModelTypeMapping.get(model_version_type)

        if base_model is None or base_model == "":
            raise InvalidArgumentError("base_model is empty")

        load_data_action = LoadDataSetAction(
            dataset=dataset, event_handler=event_handler, **kwargs
        )
        train_action = TrainAction(
            train_config=train_config,
            base_model=base_model,
            base_model_version=model_version_type,
            train_mode=TrainMode.SFT,
            event_handler=event_handler,
            **kwargs,
        )
        deploy_action = DeployAction(
            deploy_config=deploy_config, **{"event_handler": event_handler, **kwargs}
        )

        ppl = Pipeline(
            [
                load_data_action,
                train_action,
                deploy_action,
            ],
            event_handler=event_handler,
        )
        self.ppls = [ppl]
        self.result = [None]

    def start(self) -> Trainer:
        for i, ppl in enumerate(self.ppls):
            self.result[i] = ppl.exec({})
        return self

    def stop(self) -> Trainer:
        for ppl in self.ppls:
            ppl.stop()
        return self

    def resume(self) -> "LLMFinetune":
        return self
