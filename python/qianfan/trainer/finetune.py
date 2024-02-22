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
from typing import Any, Dict, List, Optional, Union

from qianfan.config import get_config
from qianfan.errors import InvalidArgumentError
from qianfan.evaluation.evaluator import Evaluator
from qianfan.model.configs import DeployConfig
from qianfan.resources.console import consts as console_consts
from qianfan.trainer.actions import (
    DeployAction,
    EvaluateAction,
    LoadDataSetAction,
    ModelPublishAction,
    TrainAction,
    action_mapping,
)
from qianfan.trainer.base import (
    BaseAction,
    EventHandler,
    Pipeline,
    Trainer,
)
from qianfan.trainer.configs import (
    ModelInfo,
    ModelInfoMapping,
    TrainConfig,
)
from qianfan.trainer.consts import (
    TrainStatus,
)


class LLMFinetune(Trainer):
    """
    Class implements the SFT training pipeline with several actions.
    Use `run()` to synchronously run the training pipeline until the
    model training is finished.
    or use `start()`, `wait()`, `stop()` to run the training asynchronously.
    """

    def __init__(
        self,
        train_type: Optional[str] = None,
        dataset: Optional[Any] = None,
        train_config: Optional[Union[TrainConfig, str]] = None,
        deploy_config: Optional[DeployConfig] = None,
        event_handler: Optional[EventHandler] = None,
        eval_dataset: Optional[Any] = None,
        evaluators: Optional[List[Evaluator]] = None,
        dataset_bos_path: Optional[str] = None,
        previous_trainer: Optional[Trainer] = None,
        previous_task_id: Optional[str] = None,
        name: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        """
        Initialization function for LLM fine-tuning.

        Parameters:
            train_type: str
                A string representing the model version type.
                like 'ERNIE-Bot-turbo-0725', 'ChatGLM2-6b'
            dataset: Dataset
                A dataset instance.
            train_config: TrainConfig
                An TrainConfig for fine-tuning training parameters.
                If not provided, default parameters of diverse
                models will be used.
            deploy_config: DeployConfig
                An DeployConfig for model service deployment parameters.
                Required if deployment is needed.
            event_handler:  EventHandler
                An EventHandler instance for receive events during
                the training process
            eval_dataset: Dataset
                An optional dataset instance for evaluation.
            evaluators: List[Evaluator]
                An list of evaluators for evaluation.
            dataset_bos_path: Optional[str]:
                deprecated, use  `dataset` instead An bos path for training,
                this will be ignored when dataset is provided.
            previous_trainer: Optional[Trainer]
                An optional previous trainer instance for incremental training.
            previous_task_id: Optional[str]
                An optional previous task id for incremental training.
            name: Optional[str]
                An optional name for the training task.

            **kwargs: Any additional keyword arguments.

        for calling example:
        ```
        sft_task = LLMFinetune(
            train_type="ERNIE-Bot-turbo-0725",
            dataset={"datasets": [{"type": 1, "id": ds_id}]},
            train_config=TrainConfig(...),
            event_handler=eh,
        )
        ```
        """
        # 设置name
        self.name = name

        if isinstance(train_config, str):
            train_config = TrainConfig.load(train_config)

        actions: List[BaseAction] = []
        # 校验dataset
        if dataset is not None:
            self.load_data_action = LoadDataSetAction(
                dataset=dataset,
                dataset_template=console_consts.DataTemplateType.NonSortedConversation,
                event_handler=event_handler,
                **kwargs,
            )
        elif dataset_bos_path:
            self.load_data_action = LoadDataSetAction(
                dataset=dataset_bos_path,
                event_handler=event_handler,
                **kwargs,
            )
        else:
            raise InvalidArgumentError("either dataset or bos_path is required")
        actions.append(self.load_data_action)
        if previous_trainer:
            # init an increment training
            if hasattr(previous_trainer, "train_action"):
                self.train_action = TrainAction(
                    train_config=train_config,
                    task_id=previous_trainer.train_action.task_id,
                    train_mode=console_consts.TrainMode.SFT,
                    job_name=name,
                    event_handler=event_handler,
                    **kwargs,
                )
            else:
                raise InvalidArgumentError(
                    "invalid trainer input without previous train action"
                )
        elif previous_task_id:
            self.train_action = TrainAction(
                train_config=train_config,
                task_id=previous_task_id,
                train_mode=console_consts.TrainMode.SFT,
                job_name=name,
                event_handler=event_handler,
                **kwargs,
            )
        else:
            # init train action from base model
            self.train_action = TrainAction(
                train_config=train_config,
                train_type=train_type,
                train_mode=console_consts.TrainMode.SFT,
                event_handler=event_handler,
                job_name=name,
                **kwargs,
            )
        actions.append(self.train_action)
        if not kwargs.get("model_not_publish"):
            self.model_publish = ModelPublishAction(
                event_handler=event_handler,
                **kwargs,
            )
            actions.append(self.model_publish)
        if deploy_config is not None:
            self.deploy_action = DeployAction(
                deploy_config=deploy_config,
                event_handler=event_handler,
            )
            actions.append(self.deploy_action)
        if eval_dataset is not None and evaluators is not None:
            self.eval_action = EvaluateAction(
                eval_dataset=eval_dataset,
                evaluators=evaluators,
                event_handler=event_handler,
            )
            actions.append(self.eval_action)
        ppl = Pipeline(
            actions=actions,
            event_handler=event_handler,
        )
        self.ppls = [ppl]
        self.result = [None]

    def run(self, **kwargs: Any) -> Trainer:
        """
        run a pipeline to run the fine-tune process.

        Parameters:
            **kwargs:
                Any additional keyword arguments.
                {"input": {}} could be specified if needed

        Raises:
            InvalidArgumentError: no pipeline bind
            to run.
        Returns:
            Trainer:
                self, for chain invocation.
        """
        self.input: Any = kwargs.get("input")
        if len(self.ppls) != 1:
            raise InvalidArgumentError("invalid pipeline to run")
        kwargs["backoff_factor"] = kwargs.get(
            "backoff_factor", get_config().TRAINER_STATUS_POLLING_BACKOFF_FACTOR
        )
        kwargs["retry_count"] = kwargs.get(
            "retry_count", get_config().TRAINER_STATUS_POLLING_RETRY_TIMES
        )
        try:
            self.result[0] = self.ppls[0].exec(**kwargs)
        except Exception as e:
            self.result[0] = {"error": e}
            raise e
        return self

    @property
    def status(self) -> str:
        """
        LLMFinetune status getter.

        Returns:
            str: status for LLMFinetune, mapping from state of actions in pipeline.
        """
        if len(self.ppls) != 1:
            raise InvalidArgumentError("invalid pipeline to get status")
        action = self.ppls[0][str(self.ppls[0].current_action)]
        if action is None:
            return TrainStatus.Unknown
        action_name = action.__class__.__name__
        return action_mapping.get(action_name, {}).get(
            action.state, TrainStatus.Unknown
        )

    def stop(self, **kwargs: Dict) -> Trainer:
        """
        stop method of LLMFinetune. LLMFinetune will stop
        all actions in pipeline. In fact, LLMFinetune only take one
        pipeline, so it will be equal to stop first of `ppls`.

        Returns:
            Trainer:
                self, for chain invocation.
        """
        # 后台运行的任务
        if self.process:
            return super().stop(**kwargs)
        else:
            for ppl in self.ppls:
                ppl.stop()
            return self

    def resume(self, **kwargs: Dict) -> "LLMFinetune":
        """
        LLMFinetune resume method.

        Returns:
            LLMFinetune:
        """
        self.result[0] = self.ppls[0].resume(**kwargs)
        return self

    @property
    def output(self) -> Any:
        return self.result[0]

    @classmethod
    def train_type_list(cls) -> Dict[str, ModelInfo]:
        return ModelInfoMapping
