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
from typing import Any, Dict, List, Optional, Union, cast

from qianfan import resources as api
from qianfan.config import get_config
from qianfan.dataset.dataset import Dataset
from qianfan.errors import InternalError, InvalidArgumentError
from qianfan.evaluation import EvaluationManager
from qianfan.evaluation.evaluator import Evaluator, LocalEvaluator, QianfanEvaluator
from qianfan.model import Model, Service
from qianfan.model.configs import DeployConfig
from qianfan.resources.console import consts as console_consts
from qianfan.trainer.base import (
    ActionState,
    BaseAction,
    with_event,
)
from qianfan.trainer.configs import (
    DefaultTrainConfigMapping,
    ModelInfoMapping,
    TrainConfig,
    TrainLimit,
)
from qianfan.utils import (
    bos_uploader,
    log_debug,
    log_error,
    log_info,
    log_warn,
    utils,
)


class LoadDataSetAction(BaseAction[Dict[str, Any], Dict[str, Any]]):
    """LoadDataSetAction
    Action for dataset's loading, invokes the dataset's save method
    to guarantee the dataset is loaded in Qianfan platform.
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

    from qianfan.dataset.dataset import Dataset

    dataset: Optional[Dataset] = None

    def __init__(
        self,
        dataset: Optional[Dataset] = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        self.dataset = dataset

    @with_event
    def exec(self, input: Dict[str, Any] = {}, **kwargs: Dict) -> Dict[str, Any]:
        return self._exec(input, **kwargs)

    def _exec(self, input: Dict[str, Any] = {}, **kwargs: Dict) -> Dict[str, Any]:
        from qianfan.dataset.data_source import BosDataSource, QianfanDataSource

        """
        Load dataset implementation, may called by exec and resume.
        """
        if self.dataset is None:
            raise InvalidArgumentError("dataset must be set")
        if self.dataset.inner_data_source_cache is None:
            raise InvalidArgumentError("invalid dataset")
        if isinstance(self.dataset.inner_data_source_cache, QianfanDataSource):
            log_debug("[load_dataset_action] prepare train-set")
            qf_data_src = cast(QianfanDataSource, self.dataset.inner_data_source_cache)
            is_released = qf_data_src.release_dataset(**kwargs)
            if not is_released:
                log_error("[load_dataset_action] dataset not released")
                raise InvalidArgumentError("dataset must be released")
            log_debug("[load_dataset_action] dataset loaded successfully")
            self.qf_dataset_id = qf_data_src.id
            return {
                "datasets": [
                    {
                        "id": qf_data_src.old_dataset_id,
                        "type": console_consts.TrainDatasetType.Platform.value,
                    }
                ]
            }
        elif isinstance(self.dataset.inner_data_source_cache, BosDataSource):
            log_debug("[load_dataset_action] prepare train-set in BOS")
            bos_data_src = cast(BosDataSource, self.dataset.inner_data_source_cache)
            return {
                "datasets": [
                    {
                        "type": console_consts.TrainDatasetType.PrivateBos.value,
                        "bosPath": bos_uploader.generate_bos_file_parent_path(
                            bos_data_src.bucket, bos_data_src.bos_file_path
                        ),
                    }
                ]
            }
        else:
            raise InvalidArgumentError("dataset must be set")

    @with_event
    def resume(self, **kwargs: Dict) -> Dict[str, Any]:
        """
        resume method for load dataset action.

        Returns:
            Dict[str, Any]: datasets metainfo including
            dataset_id and dataset_type.
        """
        if self.qf_dataset_id:
            log_debug("[load_dataset_action] dataset loading already done")
            return {
                "datasets": [
                    {
                        "id": self.qf_dataset_id,
                        "type": console_consts.TrainDatasetType.Platform.value,
                    }
                ]
            }
        log_debug("[load_dataset_action] dataset loading resumed")
        return self._exec(**kwargs)


class TrainAction(
    BaseAction[Dict[str, Any], Dict[str, Any]],
):
    """
    Class for Train Action, Synchronous invocation of the training API,
    taking a dataset metadata dict as input and producing a model metadata
    as output. Concretely, `exec` is called for running.

    Note: this action is not involved with model publishing, please use use
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

    task_id: Optional[int] = None
    """train task id"""
    job_id: Optional[int] = None
    """train job id"""
    # 这里的id新API的原因task/job和调换了，现在具体
    # task_id对应job_str_id，job_id对应task_str_id
    task_str_id: Optional[str] = None
    """train task str id"""
    job_str_id: Optional[str] = None
    """job task str id"""
    train_type: Optional[str] = ""
    """train_type"""
    base_model: Optional[str] = None
    """base train type like 'ERNIE-Bot-turbo'"""
    is_incr: bool = False
    """if it's incremental train or not"""
    train_config: Optional[TrainConfig] = None
    """train config"""
    train_mode: console_consts.TrainMode = console_consts.TrainMode.SFT
    """train mode"""
    task_name: str = ""
    """train task name"""
    task_description: Optional[str] = None
    """train task description"""
    job_description: Optional[str] = None
    """train job description"""
    _input: Optional[Dict[str, Any]] = None
    """train input"""
    result: Optional[Dict[str, Any]] = None
    """"train result"""

    def __init__(
        self,
        train_type: Optional[str] = None,
        train_config: Optional[TrainConfig] = None,
        base_model: Optional[str] = None,
        task_id: Optional[int] = None,
        job_id: Optional[int] = None,
        train_mode: Optional[console_consts.TrainMode] = None,
        task_name: Optional[str] = None,
        task_description: Optional[str] = None,
        job_description: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        """

        Parameters:
            train_type (Optional[str], optional):
                train_type, must be specified when it's not increment training
                like 'ERNIE-Bot-turbo-0725'
            train_config (Optional[TrainConfig], optional):
                train_config, e.g. `epoch=10, batch_size=32`.
            base_model (Optional[str], optional):
                base_mode, like 'ERNIE-Bot-turbo'. Defaults to None.
            task_id (Optional[int], optional):
                used in incr train, model train task_id. Defaults to None.
            job_id (Optional[int], optional):
                used in incr train, mod train job_id. Defaults to None.
            train_mode (Optional[console_consts.TrainMode], optional):
                train mode, e.g. `sft`, `incremental`. Defaults to None.
            task_name (Optional[str], optional):
                train task name. Defaults to None.
            task_description (Optional[str], optional):
                train task description. Defaults to None.
            job_description (Optional[str], optional):
                train job description. Defaults to None.
        """
        super().__init__(**kwargs)
        self.task_id = task_id
        self.job_id = job_id
        if self.task_id is not None and self.job_id is not None:
            # if incremental train
            self.is_incr = True
            self.train_config = train_config
        else:
            if train_type is None:
                raise InvalidArgumentError("train_type must be specified")
            # train from base model
            self.train_type = train_type
            if base_model is None:
                model_info = ModelInfoMapping.get(self.train_type)
                if model_info is None:
                    raise InvalidArgumentError(
                        "base_model_type must be specified caused train_type:"
                        f" {self.train_type} is not found"
                    )
                self.base_model = model_info.base_model_type
            else:
                self.base_model = base_model
            self.train_config = (
                train_config
                if train_config is not None
                else self.get_default_train_config(train_type)
            )
        self.validateTrainConfig()
        if train_mode is not None:
            self.train_mode = train_mode
        self.task_name = self._generate_task_name(task_name, self.train_type)
        self.task_description = task_description
        self.job_description = job_description

    def _generate_task_name(
        self, task_name: Optional[str], train_type: Optional[str]
    ) -> str:
        if task_name is not None:
            return task_name
        model_info = (
            ModelInfoMapping.get(train_type) if train_type is not None else None
        )
        return (
            f"job_{utils.generate_letter_num_random_id()}"
            if model_info is None
            else f"{model_info.short_name}_{utils.generate_letter_num_random_id(5)}"
        )

    def validateTrainConfig(self) -> None:
        """
        validate train_config with ModelInfo Limits

        Raises:
            InvalidArgumentError: _description_
        """
        if self.train_config is None:
            raise InvalidArgumentError("none train_config")
        if self.train_type not in ModelInfoMapping:
            log_warn(
                f"[train_action] train_type {self.train_type} not found, it may be not"
                " supported"
            )
        else:
            train_type_model_info = ModelInfoMapping[self.train_type]
            if (
                self.train_config.peft_type
                not in train_type_model_info.support_peft_types
            ):
                log_warn(
                    f"[train_action] train_type {self.train_type}, peft_type"
                    f" {self.train_config.peft_type} not found, it may be not supported"
                )
            else:
                if (
                    train_type_model_info.specific_peft_types_params_limit is not None
                    and self.train_config.peft_type
                    in train_type_model_info.specific_peft_types_params_limit
                ):
                    self._validate_train_config(
                        train_type_model_info.specific_peft_types_params_limit[
                            self.train_config.peft_type
                        ]
                        | train_type_model_info.common_params_limit,
                    )
                else:
                    self._validate_train_config(
                        train_type_model_info.common_params_limit
                    )

    def _validate_train_config(self, train_limit: TrainLimit) -> None:
        """
        validate train_config with a specific train_limit

        Args:
            train_limit (TrainLimit): _description_

        Raises:
            InvalidArgumentError: _description_
        """
        if self.train_config is None:
            raise InvalidArgumentError("validate train_config is none")
        self.train_config.validate_config(train_limit)
        self.train_config.validate_valid_fields(train_limit)

    def _exec_incremental(
        self, input: Dict[str, Any], **kwargs: Dict
    ) -> Dict[str, Any]:
        """
        increment train from task_id, job_id

        Parameters:
            input (Dict[str, Any]):
                input

        Raises:
            NotImplementedError: not implemented yet

        Returns:
            Dict[str, Any]:
                output
        """
        raise NotImplementedError("incr train not implemented")

    @with_event
    def exec(self, input: Dict[str, Any] = {}, **kwargs: Dict) -> Dict[str, Any]:
        """
        exec method for train action

        Args:
            input (Dict[str, Any], optional):
                input with dataset meta:
                for example:
                    Input:
                    ```
                    {'datasets':[{'type': 1, 'id': 111}]}
                    ```
        Raises:
            InvalidArgumentError: invalid dataset input

        Returns:
            Dict[str, Any]:
                train task output with task_id and job_id
                for example:
                    Output:
                    ```
                    {'task_id': 47923, 'job_id': 33512}
                    ```
        """
        # for resume
        if self._input is None:
            self._input = input
        return self._exec(self._input, **kwargs)

    def _exec(self, input: Dict[str, Any] = {}, **kwargs: Dict) -> Dict[str, Any]:
        # 校验数据集
        train_sets = input.get("datasets")
        if train_sets is None or len(train_sets) == 0:
            raise InvalidArgumentError("train set must be set")

        # 判断是否增量训练
        if self.is_incr:
            return self._exec_incremental(input, **kwargs)

        # request for create model train task
        assert self.train_type is not None
        assert self.base_model is not None
        resp = api.FineTune.create_task(
            name=self.task_name,
            description=self.task_description,
            train_type=self.train_type,
            base_train_type=self.base_model,
            **kwargs,
        )
        self.task_id = cast(int, resp["result"]["id"])
        self.job_str_id = resp["result"]["uuid"]
        log_debug(f"[train_action] create fine-tune task: {self.task_id}")

        assert self.train_config is not None
        req_job = {
            "taskId": self.task_id,
            "description": self.job_description,
            "baseTrainType": self.base_model,
            "trainType": self.train_type,
            "trainMode": self.train_mode.value,
            "peftType": self.train_config.peft_type,
            "trainConfig": {
                "epoch": self.train_config.epoch,
                "learningRate": self.train_config.learning_rate,
                "batchSize": self.train_config.batch_size,
                "maxSeqLen": self.train_config.max_seq_len,
                "loggingSteps": self.train_config.logging_steps,
                "warmupRatio": self.train_config.warmup_ratio,
                "weightDecay": self.train_config.weight_decay,
                "loraRank": self.train_config.lora_rank,
                "loraAllLinear": self.train_config.lora_all_linear,
                "loraAlpha": self.train_config.lora_alpha,
                "loraDropout": self.train_config.lora_dropout,
                "schedulerName": self.train_config.scheduler_name,
                **self.train_config.extras,
            },
            "trainset": train_sets,
            "trainsetRate": self.train_config.trainset_rate,
        }
        tc_dict = cast(dict, req_job["trainConfig"])
        req_job["trainConfig"] = {
            key: value for key, value in tc_dict.items() if value is not None
        }
        create_job_resp = api.FineTune.create_job(req_job, **kwargs)
        self.job_id = cast(int, create_job_resp["result"]["id"])
        self.task_str_id = create_job_resp["result"]["uuid"]
        log_debug(f"[train_action] create fine-tune job_id: {self.job_id}")

        # 获取job状态，是否训练完成
        self._wait_model_trained(**kwargs)
        self.result = {**input, "task_id": self.task_id, "job_id": self.job_id}
        assert self.result is not None
        return self.result

    def _wait_model_trained(self, **kwargs: Dict) -> None:
        if self.task_id is None or self.job_id is None:
            raise InvalidArgumentError("task_id and job_id must not be None")
        while True:
            job_status_resp = api.FineTune.get_job(
                task_id=self.task_id,
                job_id=self.job_id,
                **kwargs,
            )
            job_status = job_status_resp["result"]["trainStatus"]
            job_progress = job_status_resp["result"]["progress"]
            log_info(
                "[train_action] fine-tune running..."
                f" task_name:{self.task_name} current status: {job_status},"
                f" {job_progress}% check train task log in"
                f" https://console.bce.baidu.com/qianfan/train/sft/{self.job_str_id}/{self.task_str_id}/detail/traininglog"
            )
            if job_progress >= 50:
                log_info(f" check vdl report in {job_status_resp['result']['vdlLink']}")
            self.action_event(ActionState.Running, "train running", job_status_resp)
            if job_status == console_consts.TrainStatus.Finish:
                break
            elif job_status in [
                console_consts.TrainStatus.Fail,
                console_consts.TrainStatus.Stop,
            ]:
                log_error(
                    "[train_action] fine-tune job"
                    f" {self.job_str_id}/{self.task_str_id} has ended,"
                    f" {job_status_resp}"
                )
                break
            else:
                time.sleep(get_config().TRAIN_STATUS_POLLING_INTERVAL)
        log_info(
            "[train_action] fine-tune job has ended:"
            f" {self.job_str_id}/{self.task_str_id} with status: {job_status}"
        )

    @with_event
    def resume(self, **kwargs: Dict) -> Dict[str, Any]:
        """
        resume method for train action

        Parameters:
            **kwargs (Dict):
                input args for action resume

        """
        if self.result is not None:
            log_warn("[train_action] already done")
            return self.result
        self.action_event(ActionState.Running, "train resume")
        if self.task_id is not None and self.job_id is not None:
            log_info(
                f"[train_action] resume from created job {self.task_id}/{self.job_id}"
            )
            self._wait_model_trained(**kwargs)
            self.result = {"task_id": self.task_id, "job_id": self.job_id}
            return self.result
        else:
            if self._input is None:
                self._input = {}
            return self._exec(self._input, **kwargs)

    def stop(self, **kwargs: Dict) -> None:
        """
        stop method for train action

        Parameters:
            **kwargs (Dict):
                input args for action stop
        """
        if self.task_id is None or self.job_id is None:
            log_warn("[train_action] task_id or job_id not set, training not started")
            return
        api.FineTune.stop_job(self.task_id, self.job_id)
        log_debug(f"train job {self.task_id}/{self.job_id} stopped")

    def get_default_train_config(self, model_type: str) -> TrainConfig:
        return DefaultTrainConfigMapping.get(
            model_type,
            DefaultTrainConfigMapping[get_config().DEFAULT_FINE_TUNE_TRAIN_TYPE],
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
    {'task_id': 47923, 'job_id': 33512, 'model_id': "xxx", 'model_version_id': "aaa"}
    ```
    """

    task_id: Optional[int] = None
    """task id"""
    job_id: Optional[int] = None
    """job id"""
    result: Optional[Dict[str, Any]] = None
    """result of model publish action"""
    model: Optional[Model] = None
    """model object"""

    @with_event
    def exec(self, input: Dict[str, Any] = {}, **kwargs: Dict) -> Dict[str, Any]:
        if self.task_id == "" or self.job_id == "":
            raise InvalidArgumentError("task_id or job_id must be set")
        self.task_id = int(input.get("task_id", ""))
        self.job_id = int(input.get("job_id", ""))
        self.model = Model(task_id=self.task_id, job_id=self.job_id)
        return self._exec(input, **kwargs)

    def _exec(self, input: Dict[str, Any] = {}, **kwargs: Dict) -> Dict[str, Any]:
        if self.model is None:
            raise InvalidArgumentError("model must be set when in model publish._exec")
        log_debug("[model_publish_action] start model publish")
        try:
            self.action_event(
                ActionState.Running,
                "model publish",
                {
                    "task_id": self.task_id,
                    "job_id": self.job_id,
                },
            )
            self.model.publish(name=input.get("name", ""), **kwargs)
            log_debug(
                f"[model publish] model: {self.task_id}_{self.job_id} has been"
                " published."
            )

            self.result = {
                "task_id": self.task_id,
                "job_id": self.job_id,
                "model_id": self.model.id,
                "model_version_id": self.model.version_id,
                "model": self.model,
            }
            return self.result
        except Exception as e:
            log_error(f"[model_publish_action] model publish error: {e}")
            raise e

    @with_event
    def resume(self, **kwargs: Dict) -> Dict[str, Any]:
        # raise NotImplementedError("ModelPublishAction.resume() is not implemented")
        if self.result is not None:
            return self.result
        if self.model is not None:
            return self._exec()
        if self.task_id is None or self.job_id is None:
            raise InvalidArgumentError("task_id or job_id not set, resume failed")
        self.model = Model(task_id=self.task_id, job_id=self.job_id)
        return self._exec(**kwargs)


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
        {'task_id': 47923, 'job_id': 33512, 'model_id': "xx", 'model_version_id': "xxx"}
    output:
        ```
        {'task_id': 47923, 'job_id': 33512, 'model_id': "xx", 'model_version_id': "xxx",
        'service_id': 164, 'service_endpoint': 'xbiimimv_xxx'}
        ```
    """

    deploy_config: Optional[DeployConfig]
    """deploy config include replicas and so on"""
    model_id: Optional[int]
    """model id"""
    model_id_str: Optional[str]
    """model str id"""
    model_version_id: Optional[int]
    """model version id"""
    model_version_id_str: Optional[str]
    """model version str id """
    _input: Optional[Dict[str, Any]] = None
    """input of action"""
    result: Optional[Dict[str, Any]] = None
    """result of action"""

    def __init__(self, deploy_config: Optional[DeployConfig] = None, **kwargs: Any):
        """

        Parameters:
            deploy_config (Optional[DeployConfig], optional):
                deploy config include replicas and so on. Defaults to None.
        """
        super().__init__(**kwargs)
        self.deploy_config = deploy_config

    @with_event
    def exec(self, input: Dict[str, Any] = {}, **kwargs: Any) -> Dict[str, Any]:
        # for resume
        if self._input is None:
            self._input = input
        if self.deploy_config is None:
            raise InvalidArgumentError("deploy_config must be set")
        if input.get("model") is None:
            self.model_id = input.get("model_id")
            self.model_version_id = input.get("model_version_id")
            # TODO 迁移成str id
            if self.model_id is None or self.model_version_id is None:
                raise InvalidArgumentError("model_id or model_version_id must be set")

            self.model = Model(self.model_id, self.model_version_id, auto_complete=True)
            self.model.auto_complete_info()
        else:
            self.model = cast(Model, input.get("model"))
            if self.model is None:
                raise InvalidArgumentError(
                    "must input with model or model id and version id"
                )
            self.model.auto_complete_info()
            self.model_id = self.model.old_id
            self.model_version_id = self.model.old_version_id
        # 自动补全

        return self._exec(**kwargs)

    def _exec(self, input: Dict[str, Any] = {}, **kwargs: Dict) -> Dict[str, Any]:
        if self.deploy_config is None:
            raise InvalidArgumentError("deploy_config must be set in deploy._exec")
        log_debug(
            f"[deploy_action] try deploy model {self.model.id}_{self.model.version_id}"
        )
        self.action_event(
            ActionState.Running,
            "ready to deploy",
            {
                "model": self.model,
            },
        )
        # deploy model
        self.model.deploy(self.deploy_config, **kwargs)
        if self.model.service is not None:
            log_debug(
                "[deploy_action] model"
                f" {self.model_id}_{self.model_version_id} deployed successfully with"
                " service:"
                f" {self.model.service.id} endpoint:{self.model.service.endpoint}"
            )
            return {
                **input,
                "service_id": self.model.service.id,
                "service_endpoint": self.model.service.endpoint,
                "service": self.model.service,
                "model": self.model,
            }
        else:
            raise InternalError("model.service is not available")

    @with_event
    def resume(self, **kwargs: Dict) -> Dict[str, Any]:
        """
        resume method for deploy action

        Parameters:
            **kwargs (Dict):
                input args for action resume

        """
        if self.model_id is not None and self.model_version_id is not None:
            self.model = Model(self.model_id_str, self.model_version_id_str)
            self.model.auto_complete_info()
        elif self.model is None:
            raise InvalidArgumentError(
                "either (model_id and version_id) or model must be set"
            )
        return self._exec()


class EvaluateAction(BaseAction[Dict[str, Any], Dict[str, Any]]):
    """EvaluateAction
    Action for evaluate models or services.
    Sample:
    input:
        ```
        {'model_id': 47923, 'model_version_id': 33512}
        ```
    output:
        ```
        {'eval_res': EvaluationResult ...}
        ```
    """

    eval_manager: Optional[EvaluationManager] = None
    """evaluation manager for evaluate models or services."""
    eval_dataset: Optional[Dataset] = None
    _input: Optional[Dict[str, Any]] = None
    """input of action"""
    result: Optional[Dict[str, Any]] = None
    """result of action"""

    def __init__(
        self, eval_dataset: Dataset, evaluators: List[Evaluator], **kwargs: Any
    ):
        """
        init method for evaluate action

        Parameters:
            eval_dataset Dataset:
                dataset for evaluation, use Dataset.load() to create.
            evaluators List[Evaluator]:
                evaluators for evaluation, include local and qianfan remote evaluators.
                Specifically, qianfan_evaluators are only available for Model.
        """
        super().__init__(**kwargs)
        self.eval_dataset = eval_dataset
        local_evaluators = [
            eval for eval in evaluators if isinstance(eval, LocalEvaluator)
        ]
        qianfan_evaluators = [
            eval for eval in evaluators if isinstance(eval, QianfanEvaluator)
        ]
        self.eval_manager = EvaluationManager(
            local_evaluators=local_evaluators if len(local_evaluators) > 0 else None,
            qianfan_evaluators=(
                qianfan_evaluators if len(qianfan_evaluators) > 0 else None
            ),
        )

    @with_event
    def exec(self, input: Dict[str, Any] = {}, **kwargs: Any) -> Dict[str, Any]:
        """
        exec evaluation

        Parameters:
            input (Dict[str, Any], optional): input dict with model/service info.
            Defaults to {}.

        Returns:
            Dict[str, Any]: output the result with the original input
        """
        self._input = input
        log_info(f"[evaluation_action] begin to do evaluation, input: {self._input}")
        llm = self._parse_from_input(self._input)
        res = self._exec(llm, **kwargs)
        self.result = {"eval_res": res, **input}
        return self.result

    def _parse_from_input(self, input: Dict[str, Any] = {}) -> Union[Model, Service]:
        """
        Parses and returns the model or service object based on the input parameters.

        Parameters:
            input (Dict[str, Any], optional): . Defaults to {}.

        Returns:
            Union[Model, Service]: parsed model or service object
        """

        if input.get("service"):
            llm = input.get("service")
        elif input.get("model"):
            llm = input.get("model")
        elif input.get("model_id") and input.get("model_version_id"):
            llm = Model(input["model_id"], input["model_version_id"])
        else:
            log_error(f"[evaluation_action] invalid llm input error {self._input}")
            raise InvalidArgumentError(
                "model or service must be set in evaluation action"
            )
        assert isinstance(llm, (Model, Service))
        return llm

    def _exec(self, llm: Union[Model, Service], **kwargs: Dict) -> Any:
        """
        accept a llm model/service to do evaluation

        Parameters:
            llm (Union[Model, Service]): model to do evaluation

        Returns:
            Any: evaluation result object
        """
        assert self.eval_manager is not None
        if self.eval_dataset is None:
            raise InvalidArgumentError("eval_dataset must be set")
        self.action_event(
            ActionState.Running,
            "ready to evaluate",
            {
                "llm": llm,
                "dataset": self.eval_dataset,
            },
        )
        log_info("[evaluation_action] running evaluation...")
        return self.eval_manager.eval([llm], self.eval_dataset, **kwargs)

    @with_event
    def resume(self, **kwargs: Dict) -> Dict[str, Any]:
        """
        resume method for eval action

        Parameters:
            **kwargs (Dict):
                input args for action resume

        """
        if self._input is None:
            log_error(
                "[evaluation_action] previous input not found, call run() instead."
            )
            raise ValueError("input not found")
        llm = self._parse_from_input(self._input)
        res = self._exec(llm, **kwargs)
        self.result = {"eval_res": res, **self._input}
        return self.result
