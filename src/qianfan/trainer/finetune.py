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
from typing import Any, Dict, List, Optional, Union, cast

from qianfan.config import get_config
from qianfan.dataset.data_source import BosDataSource, QianfanDataSource
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
    ActionState,
    FinetuneStatus,
    ServiceStatus,
)


class LLMFinetune(Trainer):
    """
    Class implements the SFT training pipeline with several actions.
    Use `run()` to synchronously run the training pipeline until the
    model training is finished.
    """

    def __init__(
        self,
        train_type: str,
        dataset: Optional[Any] = None,
        train_config: Optional[Union[TrainConfig, str]] = None,
        deploy_config: Optional[DeployConfig] = None,
        event_handler: Optional[EventHandler] = None,
        base_model: Optional[str] = None,
        eval_dataset: Optional[Any] = None,
        evaluators: Optional[List[Evaluator]] = None,
        dataset_bos_path: Optional[str] = None,
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
            base_model:
                An optional string representing the base model like
                'ERNIE-Bot-turbo', 'ChatGLM2'
                which will be mapped from the model version type if
                not set.
            eval_dataset: Dataset
                An optional dataset instance for evaluation.
            evaluators: List[Evaluator]
                An list of evaluators for evaluation.
            bos_path: Optional[str]:
                An bos path for training, this will be ignored
                if dataset is provided.
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
        # 校验train_type
        if train_type is None or train_type == "":
            raise InvalidArgumentError("train_type is empty")

        if isinstance(train_config, str):
            train_config = TrainConfig.load(train_config)

        actions: List[BaseAction] = []
        # 校验dataset
        if dataset is not None:
            if dataset.inner_data_source_cache is None:
                raise InvalidArgumentError("invalid dataset")
            if isinstance(dataset.inner_data_source_cache, QianfanDataSource):
                qf_data_src = cast(QianfanDataSource, dataset.inner_data_source_cache)
                if (
                    qf_data_src.template_type
                    != console_consts.DataTemplateType.NonSortedConversation
                ):
                    raise InvalidArgumentError(
                        "dataset must be `non-sorted conversation` template in"
                        " llm-fine-tune"
                    )
                self.load_data_action = LoadDataSetAction(
                    dataset=dataset, event_handler=event_handler, **kwargs
                )
            elif isinstance(dataset.inner_data_source_cache, BosDataSource):
                self.load_data_action = LoadDataSetAction(
                    dataset=dataset, event_handler=event_handler, **kwargs
                )
            else:
                raise InvalidArgumentError(
                    "dataset must be either implemented with QianfanDataSource or"
                    " BosDataSource"
                )
            actions.append(self.load_data_action)
        elif dataset_bos_path:
            self.dataset_bos_path = dataset_bos_path
        else:
            raise InvalidArgumentError("either dataset or bos_path is required")
        self.train_action = TrainAction(
            train_config=train_config,
            base_model=base_model,
            train_type=train_type,
            train_mode=console_consts.TrainMode.SFT,
            event_handler=event_handler,
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
            )
            actions.append(self.eval_action)
        ppl = Pipeline(
            actions=actions,
            event_handler=event_handler,
        )
        self.ppls = [ppl]
        self.result = [None]

    def run(self, **kwargs: Any) -> Trainer:
        """_summary_
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
        if not hasattr(self, "load_data_action") and self.dataset_bos_path is not None:
            kwargs["input"] = {
                "datasets": [{"id": 2, "bosPath": self.dataset_bos_path}]
            }
        self.result[0] = self.ppls[0].exec(**kwargs)
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
        action = self.ppls[0][str(self.ppls[0]._state)]
        if action is None:
            return FinetuneStatus.Unknown
        action_name = action.__class__.__name__
        return fine_tune_action_mapping.get(action_name, {}).get(
            action.state, FinetuneStatus.Unknown
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
        for ppl in self.ppls:
            ppl.stop()
        return self

    def resume(self, **kwargs: Dict) -> "LLMFinetune":
        """
        LLMFinetune resume method.

        Returns:
            LLMFinetune: _description_
        """
        self.result[0] = self.ppls[0].resume(**kwargs)
        return self

    @property
    def output(self) -> Any:
        return self.result[0]

    @classmethod
    def train_type_list(cls) -> Dict[str, ModelInfo]:
        return ModelInfoMapping


# mapping for action state -> fine-tune status
fine_tune_action_mapping: Dict[str, Dict[str, Any]] = {
    LoadDataSetAction.__class__.__name__: {
        ActionState.Preceding: FinetuneStatus.DatasetLoading,
        ActionState.Running: FinetuneStatus.DatasetLoading,
        ActionState.Done: FinetuneStatus.DatasetLoaded,
        ActionState.Error: FinetuneStatus.DatasetLoadFailed,
        ActionState.Stopped: FinetuneStatus.DatasetLoadStopped,
    },
    TrainAction.__class__.__name__: {
        ActionState.Preceding: FinetuneStatus.TrainCreated,
        ActionState.Running: FinetuneStatus.Training,
        ActionState.Done: FinetuneStatus.TrainFinished,
        ActionState.Error: FinetuneStatus.TrainFailed,
        ActionState.Stopped: FinetuneStatus.TrainStopped,
    },
    ModelPublishAction.__class__.__name__: {
        ActionState.Preceding: FinetuneStatus.ModelPublishing,
        ActionState.Running: FinetuneStatus.ModelPublishing,
        ActionState.Done: FinetuneStatus.ModelPublished,
        ActionState.Error: FinetuneStatus.ModelPublishFailed,
        ActionState.Stopped: FinetuneStatus.ModelPublishFailed,
    },
    DeployAction.__class__.__name__: {
        ActionState.Preceding: ServiceStatus.Created,
        ActionState.Running: ServiceStatus.Deploying,
        ActionState.Done: ServiceStatus.Deployed,
        ActionState.Error: ServiceStatus.DeployFailed,
        ActionState.Stopped: ServiceStatus.DeployStopped,
    },
    EvaluateAction.__class__.__name__: {
        ActionState.Preceding: FinetuneStatus.EvaluationCreated,
        ActionState.Running: FinetuneStatus.EvaluationRunning,
        ActionState.Done: FinetuneStatus.EvaluationFinished,
        ActionState.Error: FinetuneStatus.EvaluationFailed,
        ActionState.Stopped: FinetuneStatus.EvaluationStopped,
    },
}
