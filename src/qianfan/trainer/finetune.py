import time
import uuid
from typing import Any, Dict, Optional

from pydantic import BaseModel, root_validator
from qianfan import resources as api
from qianfan.errors import InvalidArgumentError
from qianfan.trainer.base import BaseAction, Event, EventHandler, Pipeline, Trainer
from qianfan.trainer.configs import DeployConfig, TrainConfig
from qianfan.trainer.consts import (
    ActionState,
    ModelTypeMapping,
    ServiceStatus,
    TrainMode,
)
from qianfan.trainer.event import EventHandler


class TrainAction(
    BaseAction[Dict[str, Any], Dict[str, Any]],
):
    is_incr: bool = False

    def __init__(
        self,
        train_config: TrainConfig = None,
        base_model: Optional[str] = None,
        base_model_version: str = None,
        model_type: str = None,
        task_id: str = None,
        job_id: str = None,
        train_mode: TrainMode = None,
        **kwargs: Any
    ) -> None:
        super().__init__(**kwargs)
        self.train_config = train_config
        self.base_model = base_model
        self.base_model_version = base_model_version
        self.model_type = ModelTypeMapping.get(model_type)
        self.task_id = task_id
        self.task_id = job_id
        self.train_mode = train_mode

    def exec(self, input: Dict[str, Any], **kwargs) -> Any:
        print("hi1111", input)
        # request for create model train task
        try:
            resp = api.FineTune.create_task(name=str(uuid.uuid4()))
            print("create task", resp)
        except Exception as e:
            self._event_dispatcher.dispatch(
                Event(
                    self.id,
                    ActionState.Error,
                    "action_error: action[{}], msg:{}".format(self.id, e),
                )
            )
            print("create task error", e)
            return None
        self.task_id = resp["result"]["id"]

        train_sets = input.get("datasets")
        if train_sets is None or len(train_sets) == 0:
            self._event_dispatcher.dispatch(
                Event(
                    self.id,
                    ActionState.Error,
                    "action_error: action[{}], msg:{}".format(self.id, "no trainset"),
                )
            )
            return None

        # request for model train job
        try:
            # print('reqjob', self。)
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
            print("reqjob", req_job)
            create_job_resp = api.FineTune.create_job(req_job)
            print("create task", resp)
        except Exception as e:
            # self._event_dispatcher.dispatch(
            #     Event(
            #         self.id,
            #         ActionState.Error,
            #         "action_error: action[{}], msg:{}".format(self.id, e),
            #     )
            # )
            print("create job error", e)
            return None
        self.job_id = create_job_resp["result"]["id"]
        while True:
            try:
                job_status_resp = api.FineTune.get_job(
                    task_id=self.task_id, job_id=self.job_id
                )
                job_status = job_status_resp["result"]["trainStatus"]
            except Exception as e:
                self._event_dispatcher.dispatch(
                    Event(
                        self.id,
                        ActionState.Error,
                        "action_error: action[{}], msg:{}".format(self.id, e),
                    )
                )
                return None
            print("job status:", job_status)
            if job_status != "RUNNING":
                break
            time.sleep(10)

        try:
            model_publish_resp = api.Model.publish(
                is_new=True,
                model_name="test_sdk_ebt1",
                version_meta={"taskId": self.task_id, "iterationId": self.job_id},
            )
            # 获取model_id and version
            self.model_id = model_publish_resp["result"]["modelId"]
            self.model_version = model_publish_resp["result"]["version"]
            print("model_id:", self.model_id)
            print("model_version", self.model_version)

            while True:
                try:
                    job_status_resp = api.FineTune.get_job(
                        task_id=self.task_id, job_id=self.job_id
                    )
                    job_status = job_status_resp["result"]["trainStatus"]
                except Exception as e:
                    self._event_dispatcher.dispatch(
                        Event(
                            self.id,
                            ActionState.Error,
                            "action_error: action[{}], msg:{}".format(self.id, e),
                        )
                    )
                    return None
                print("job status:", job_status)
                if job_status != "RUNNING":
                    break
                time.sleep(10)

            # 获取模型版本信息：
            model_list_resp = api.Model.list(model_id=self.model_id)
            print("get model list", model_list_resp["result"])
            model_version_list = model_list_resp["result"]["modelVersionList"]
            # print("model:", m)
            # if m["modelId"] == self.model_id and m["version"] == self.model_version:
            # print("match version:==>")
            print("first version:", model_version_list[0])
            if model_version_list is None or len(model_version_list) == 0:
                return ValueError("not model version matched")
            self.model_version_id = model_version_list[0]["modelVersionId"]
            print("model_version_id", self.model_version_id)

            # 获取模型版本详情
            # 模型版本状态有三种：Creating, Ready, Failed
            while True:
                model_detail_info = api.Model.detail(
                    model_version_id=self.model_version_id
                )
                model_version_state = model_detail_info["result"]["state"]
                print("current model_version_state:", model_version_state)
                if model_version_state != "Creating":
                    break
                time.sleep(20)

        except Exception as e:
            print("publish model error", e)
            return None
        return {"model_id": self.model_id, "model_version_id": self.model_version_id}


class DeployAction(BaseAction[Dict[str, Any], Dict[str, Any]]):
    deploy_config: Optional[DeployConfig]
    model_id: Optional[str] = None
    model_version_id: Optional[str] = None

    def __init__(self, deploy_config: Optional[DeployConfig] = None, **kwargs: Dict):
        self.deploy_config = deploy_config

    def exec(self, input: Dict[str, Any], **kwargs: Dict) -> Dict[str, Any] | None:
        if self.deploy_config is None:
            return input
        self.model_id = input.get("model_id", "")
        self.mdoel_version_id = input.get("model_version_id", "")
        if self.model_id == "" or self.mdoel_version_id == "":
            return
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

        # 资源付费完成后，serviceStatus会变成Deploying，查看模型服务状态, 直到serviceStatus变成部署完成，得到model_endpoint
        # 这一步涉及到资源调度，需要等待5-20分钟不等
        while True:
            resp = api.Service.get(id=self.svc_id)
            svc_status = resp["result"]["serviceStatus"]
            print("svc deploy status:", svc_status)
            if svc_status != ServiceStatus.Deploying.value:
                sft_model_endpoint = resp["result"]["uri"]
                break
            time.sleep(20)
        print("sft_model_endpoint:", sft_model_endpoint)
        return {"service_id": self.svc_id, "model_endpoint": sft_model_endpoint}


class LoadDataSetAction(BaseAction[Dict[str, Any], Dict[str, Any]]):
    dataset: Any

    def __init__(
        self,
        dataset: Any = None,
        event_handler: Optional[EventHandler] = None,
        **kwargs
    ) -> None:
        super().__init__()
        self.dataset = dataset

    def exec(
        self, input: Dict[str, Any] | None = None, **kwargs: Dict
    ) -> Dict[str, Any] | None:
        if isinstance(self.dataset, Dict):
            return self.dataset
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
            deploy_config=deploy_config, event_handler=event_handler, **kwargs
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

    def stop(self):
        for ppl in self.ppls:
            ppl.stop({})
        return self
