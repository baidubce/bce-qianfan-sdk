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
import time
from typing import Any, Dict, Optional, cast

from qianfan import resources as api
from qianfan.config import get_config
from qianfan.dataset.dataset import Dataset, QianfanDataSource
from qianfan.errors import InternalError, InvalidArgumentError
from qianfan.resources.console import consts as console_consts
from qianfan.trainer.base import (
    BaseAction,
    EventHandler,
    with_event,
)
from qianfan.trainer.configs import DefaultTrainConfigMapping, DeployConfig, TrainConfig
from qianfan.trainer.consts import (
    ModelTypeMapping,
)
from qianfan.trainer.model import Model
from qianfan.utils import log_debug, utils


class TrainAction(
    BaseAction[Dict[str, Any], Dict[str, Any]],
):
    """
    Class for Train Action, Synchronous invocation of the training API,
    taking a dataset metainfo dict as input and producing a model metadata
    as output. Concretly, `exec` is called for running.

    Note: this action is not involved with model publising, please use use
    `ModelPublishAction` for publishing model.

    Sample:

    Input:
    ```
    {'datasets':[{'type': 1, 'id': 111}]}
    ```

    Output:
    ```
    {'task_id': 47923, 'job_id': 33512}
    Sample code:
    ```
    """

    is_incr: bool = False

    def __init__(
        self,
        train_type: str,
        train_config: Optional[TrainConfig] = None,
        base_model: Optional[str] = None,
        task_id: Optional[int] = None,
        job_id: Optional[int] = None,
        **kwargs: Any,
    ) -> None:
        """_summary_

        Args:
            train_type (str):
                train_type, like 'ERNIE-Bot-turbo-0725'
            train_config (Optional[TrainConfig], optional):
                train_config, e.g. `epoch=10, batch_size=32`.
            base_model (Optional[str], optional):
                base_mode, like 'ERNIE-Bot-turbo'. Defaults to None.
            task_id (Optional[int], optional):
                used in incr train, model train task_id. Defaults to None.
            job_id (Optional[int], optional):
                used in incr train, mod train job_id. Defaults to None.
        """
        super().__init__(**kwargs)
        self.task_id = task_id
        self.job_id = job_id
        if self.task_id is not None or self.job_id is not None:
            # if incremental train
            self.is_incr = True
        else:
            # train from base model
            self.train_type = train_type
            self.base_model = (
                ModelTypeMapping.get(self.train_type)
                if base_model is None
                else base_model
            )
        self.train_config = (
            train_config
            if train_config is not None
            else self.get_default_train_config(train_type)
        )
        self.train_mode: str = console_consts.TrainMode.SFT.value

    def _exec_incremental(
        self, input: Dict[str, Any], **kwargs: Dict
    ) -> Dict[str, Any]:
        raise NotImplementedError("incr train not implemented")

    @with_event
    def exec(self, input: Dict[str, Any] = {}, **kwargs: Dict) -> Dict[str, Any]:
        if self.is_incr:
            return self._exec_incremental(input, **kwargs)
        # request for create model train task
        self.task_name = f"task_{utils.generate_letter_num_random_id()}"
        resp = api.FineTune.create_task(self.task_name)
        self.task_id = cast(int, resp["result"]["id"])
        log_debug(f"[train_action] create fine-tune task: {self.task_id}")

        train_sets = input.get("datasets")
        if train_sets is None or len(train_sets) == 0:
            raise InvalidArgumentError("trainset rate must be set")
        assert self.train_config is not None
        req_job = {
            "taskId": self.task_id,
            "baseTrainType": self.base_model,
            "trainType": self.train_type,
            "trainMode": self.train_mode,
            "peftType": self.train_config.peft_type,
            "trainConfig": {
                "epoch": self.train_config.epoch,
                "learningRate": self.train_config.learning_rate,
                "batchSize": self.train_config.batch_size,
                "maxSeqLen": self.train_config.max_seq_len,
            },
            "trainset": train_sets,
            "trainsetRate": self.train_config.trainset_rate,
        }
        tc_dict = cast(dict, req_job["trainConfig"])
        req_job["trainConfig"] = {
            key: value for key, value in tc_dict.items() if value is not None
        }
        create_job_resp = api.FineTune.create_job(req_job)
        self.job_id = cast(int, create_job_resp["result"]["id"])
        log_debug(f"[train_action] create fine-tune job_id: {self.job_id}")

        # 获取job状态，是否训练完成
        while True:
            job_status_resp = api.FineTune.get_job(
                task_id=self.task_id, job_id=self.job_id
            )
            job_status = job_status_resp["result"]["trainStatus"]
            if job_status != console_consts.TrainStatus.Running:
                break
            time.sleep(get_config().TRAIN_STATUS_POLLING_INTERVAL)

        log_debug(
            f"[train_action] fine-tune job has ended: {self.job_id} with status:"
            f" {job_status}"
        )
        return {"task_id": self.task_id, "job_id": self.job_id}

    def resume(self, input: Dict[str, Any], **kwargs: Dict) -> None:
        return self.exec(input, **kwargs)

    def get_default_train_config(self, model_type: str) -> TrainConfig:
        return DefaultTrainConfigMapping.get(
            model_type, DefaultTrainConfigMapping["ERNIE-Bot-turbo-0725"]
        )


class ModelPublishAction(BaseAction[Dict[str, Any], Dict[str, Any]]):
    """
    Class for Model publish action, Commonly used after `TrainAction`.

    Sample:

    Input:
    ```
    {'task_id': 47923, 'job_id': 33512}
    ```

    Output:
    ```
    {'task_id': 47923, 'job_id': 33512, 'model_id': 1, 'model_version_id': 39}
    ```
    """

    @with_event
    def exec(self, input: Dict[str, Any] = {}, **kwargs: Dict) -> Dict[str, Any]:
        self.task_id = int(input.get("task_id", ""))
        self.job_id = int(input.get("job_id", ""))
        model = Model(task_id=self.task_id, job_id=self.job_id)
        if self.task_id == "" or self.job_id == "":
            raise InvalidArgumentError("task_id or job_id must be set")

        model.publish()
        log_debug(
            f"[model_publish_action] model: {self.task_id}_{self.job_id} has been"
            " published."
        )
        output = {
            "task_id": self.task_id,
            "job_id": self.job_id,
            "model_id": model.id,
            "model_version_id": model.version_id,
        }
        return output

    def resume(self, input: Dict[str, Any], **kwargs: Dict) -> None:
        return self.exec(input, **kwargs)


class LoadDataSetAction(BaseAction[Dict[str, Any], Dict[str, Any]]):
    """LoadDataSetAction
    Action for dataset's loading, invokes the dataset's save method
    to gaurantee the dataset is loaded in Qianfan platform.
    Sample:
        ```
        load_action = LoadDataSetAction(dataset=Dataset(id=1))
        load_action.exec()
        ```

    input:
        none
    output:
        ```
        {"datasets" : [{"id": 1, "name": "test_dataset"}]}
        ```
    """

    dataset: Optional[Dataset] = None

    def __init__(
        self,
        dataset: Optional[Dataset] = None,
        event_handler: Optional[EventHandler] = None,
        **kwargs: Dict[str, Any],
    ) -> None:
        super().__init__(event_handler=event_handler)
        self.dataset = dataset

    @with_event
    def exec(self, input: Dict[str, Any] = {}, **kwargs: Dict) -> Dict[str, Any]:
        if self.dataset is None:
            raise InvalidArgumentError("dataset must be set")
        if self.dataset.inner_data_source_cache is None:
            raise InvalidArgumentError("invalid dataset")
        if not isinstance(self.dataset.inner_data_source_cache, QianfanDataSource):
            raise InvalidArgumentError(
                "dataset must be saved to qianfan before fine-tune"
            )
        log_debug("[load_dataset_action] prepared to do get train-set")
        qf_data_src = cast(QianfanDataSource, self.dataset.inner_data_source_cache)
        is_released = qf_data_src.release_dataset()
        if not is_released:
            raise InvalidArgumentError("dataset must be released")
        if (
            qf_data_src.template_type
            != console_consts.DataTemplateType.NonSortedConversation
        ):
            raise InvalidArgumentError("dataset must be `sorted conversation` template")
        log_debug("[load_dataset_action] dataset loaded successfully")
        return {
            "datasets": [
                {
                    "id": qf_data_src.id,
                    "type": console_consts.TrainDatasetType.Platform.value,
                }
            ]
        }

    def resume(self, input: Dict[str, Any], **kwargs: Dict) -> None:
        return None


class DeployAction(BaseAction[Dict[str, Any], Dict[str, Any]]):
    """DeployAction
    Action for model service deployment. A TrainConfig must be supplied
    when instance initialized.
    Sample:
        ```
        deploy_config = DeployConfig(replicas=1, pool_type=1)
        deploy_action = DeployAction(deploy_config=deploy_config)

        output = deploy_action.exec(input)
        ```

    input:
        {'task_id': 47923, 'job_id': 33512, 'model_id': 1, 'model_version_id': 39}
    output:
        ```
        {'task_id': 47923, 'job_id': 33512, 'model_id': 1, 'model_version_id': 39,
        'service_id': 164, 'service_endpoint': 'xbiimimv_xxx'}
        ```
    """

    deploy_config: Optional[DeployConfig]
    model_id: Optional[int]
    model_version_id: Optional[int]

    def __init__(
        self, deploy_config: Optional[DeployConfig] = None, **kwargs: Dict[str, Any]
    ):
        super().__init__(kwargs=kwargs)
        self.deploy_config = deploy_config

    @with_event
    def exec(self, input: Dict[str, Any], **kwargs: Dict) -> Dict[str, Any]:
        if self.deploy_config is None:
            raise InvalidArgumentError("deploy_config must be set")
        self.model_id = input.get("model_id")
        self.model_version_id = input.get("model_version_id")
        if self.model_id is None or self.model_version_id is None:
            raise InvalidArgumentError("model_id or model_version_id must be set")
        log_debug(
            f"[deploy_action] try deploy model {self.model_id}_{self.model_version_id}"
        )
        model = Model(self.model_id, self.model_version_id)
        model.deploy(self.deploy_config)
        if model.service is not None:
            log_debug(
                "[deploy_action] model"
                f" {self.model_id}_{self.model_version_id} deployed successfully with"
                f" service: {model.service.id} endpoint:{model.service.endpoint}"
            )
            return {
                "service_id": model.service.id,
                "service_endpoint": model.service.endpoint,
            }
        else:
            raise InternalError("model.service is not avaiable")

    def resume(self, input: Dict[str, Any], **kwargs: Dict) -> None:
        return None
