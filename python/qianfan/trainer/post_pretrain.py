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

from qianfan.common.persister.persist import FilePersister
from qianfan.config import encoding, get_config
from qianfan.dataset import Dataset
from qianfan.errors import InvalidArgumentError
from qianfan.resources.console import consts as console_consts
from qianfan.trainer.actions import (
    LoadDataSetAction,
    TrainAction,
    action_mapping,
)
from qianfan.trainer.base import (
    BaseAction,
    EventHandler,
)
from qianfan.trainer.configs import (
    DatasetConfig,
    ModelInfo,
    TrainConfig,
    get_trainer_model_list,
)
from qianfan.trainer.consts import (
    TrainStatus,
)
from qianfan.trainer.pipeline import Pipeline
from qianfan.trainer.trainer import Trainer


class PostPreTrain(Trainer):
    """
    Class implements the PostPreTrain training pipeline with several actions.
    Use `run()` to synchronously run the training pipeline until the
    model training pipeline is finished.
    """

    def __init__(
        self,
        train_type: Optional[str] = None,
        dataset: Optional[Union[DatasetConfig, Dataset, str]] = None,
        train_config: Optional[Union[TrainConfig, str]] = None,
        event_handler: Optional[EventHandler] = None,
        name: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        """
        Initialization function for LLM post-pretrain.

        Parameters:
            train_type: str
                A string representing the model version type.
                like 'ERNIE-Speed'
            dataset: Optional[Union[Dataset, str]] = None,
                A post_pretrain dataset instance and an bos path.
                or an bos path for post pretrain
            train_config: TrainConfig
                An TrainConfig for post pretrain training parameters.
                If not provided, default parameters of diverse
                models will be used.
            event_handler:  EventHandler
                An EventHandler instance for receive events during
                the training process
            name: Optional[str]
                An optional name for the training task.

            **kwargs: Any additional keyword arguments.

        for calling example:
        ```
        ds = Dataset.load(qianfan_dataset_id="", ...)
        sft_task = PostPreTrain(
            train_type="ERNIE-Speed-8K",
            dataset=ds,
            train_config=TrainConfig(...),
            event_handler=eh,
        )
        ```
        """
        # 设置name
        self.name = name

        # 校验train_type
        if train_type is None or train_type == "":
            raise InvalidArgumentError("train_type is empty")

        if isinstance(train_config, str):
            train_config = TrainConfig.load(train_config)

        actions: List[BaseAction] = []
        # 初始化load action
        assert dataset is not None
        self.load_data_action = LoadDataSetAction(
            dataset,
            console_consts.DataTemplateType.GenericText,
            event_handler=event_handler,
            **kwargs,
        )
        actions.append(self.load_data_action)
        # 初始化train action
        self.train_action = TrainAction(
            train_config=train_config,
            train_type=train_type,
            train_mode=console_consts.TrainMode.PostPretrain,
            event_handler=event_handler,
            job_name=name,
            **kwargs,
        )
        actions.append(self.train_action)
        ppl = Pipeline(
            actions=actions,
            event_handler=event_handler,
        )
        self.ppls = [ppl]
        self.result = [None]

    def from_ppl(self, ppl: Optional[Pipeline]) -> "Trainer":
        """
        create a trainer from pipeline.
        Returns:
            Trainer: self, for chain invocation.
        """
        if ppl is None:
            raise ValueError("invalid pipeline to create trainer")
        assert len(ppl) >= 2
        for ac in ppl:
            if isinstance(ac, LoadDataSetAction):
                self.load_data_action = ac
            elif isinstance(ac, TrainAction):
                self.train_action = ac
        self.ppls = [ppl]
        return self

    def run(self, **kwargs: Any) -> Trainer:
        """
        run a pipeline to run the post-pretrain process.

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
        self.result[0] = self.ppls[0].exec(**kwargs)
        return self

    @property
    def status(self) -> str:
        """
        PostPreTrain status getter.

        Returns:
            str: status for PostPreTrain, mapping from state of actions in pipeline.
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

    @property
    def output(self) -> Any:
        return self.result[0]

    @classmethod
    def train_type_list(cls) -> Dict[str, ModelInfo]:
        return get_trainer_model_list(console_consts.TrainMode.PostPretrain)

    @staticmethod
    def list() -> List["Trainer"]:
        local_trainer_ppl = FilePersister.list(Pipeline)
        trainer_list: List["Trainer"] = []
        for task_ppl in local_trainer_ppl:
            try:
                assert isinstance(task_ppl, Pipeline)
                if (
                    task_ppl._case_init_params is not None
                    and task_ppl._case_init_params.get("case_type")
                    == PostPreTrain.__name__
                ):
                    trainer_inst = PostPreTrain(pipeline=task_ppl)
                    trainer_list.append(trainer_inst)
            except Exception as e:
                raise e

        return trainer_list

    @staticmethod
    def load(id: Optional[str] = None, file: Optional[str] = None) -> "Trainer":
        if file is not None:
            with open(file=file, mode="rb") as f:
                task_ppl = Pipeline.load(f.read())
        elif id:
            task_ppl = cast(Pipeline, FilePersister.load(id, Pipeline))
        else:
            raise InvalidArgumentError("invalid id or file to load")
        assert isinstance(task_ppl, Pipeline)
        if (
            task_ppl._case_init_params is not None
            and task_ppl._case_init_params.get("case_type") == PostPreTrain.__name__
        ):
            trainer_inst = PostPreTrain(pipeline=task_ppl)
            return trainer_inst

        raise InvalidArgumentError("pipeline not found {id} to load")

    def save(self, file: Optional[str] = None) -> None:
        if file:
            with open(file=file, mode="w", encoding=encoding()) as f:
                f.write(self.ppls[0].persist().decode(encoding=encoding()))
        else:
            FilePersister.save(self.ppls[0])

    def info(self) -> Dict:
        return self.ppls[0]._action_dict()

    @property
    def id(self) -> str:
        return self.ppls[0].id
