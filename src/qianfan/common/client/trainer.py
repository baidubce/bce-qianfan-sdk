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
from typing import Any, Callable, Dict, Optional

import typer
from rich.console import Console
from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TaskID,
    TaskProgressColumn,
    TextColumn,
    TimeElapsedColumn,
)

from qianfan.common.client.utils import (
    credential_required,
    enum_typer,
    print_error_msg,
    replace_logger_handler,
)
from qianfan.dataset import Dataset
from qianfan.errors import InternalError
from qianfan.model.configs import DeployConfig
from qianfan.model.consts import ServiceType
from qianfan.resources.console.consts import DeployPoolType
from qianfan.trainer import LLMFinetune
from qianfan.trainer.actions import (
    DeployAction,
    EvaluateAction,
    LoadDataSetAction,
    ModelPublishAction,
    TrainAction,
)
from qianfan.trainer.base import Pipeline
from qianfan.trainer.consts import ActionState, PeftType
from qianfan.trainer.event import Event, EventHandler

trainer_app = typer.Typer(
    no_args_is_help=True,
    help="Qianfan trainer",
    context_settings={"help_option_names": ["-h", "--help"]},
)


class MyEventHandler(EventHandler):
    def __init__(self, console: Console) -> None:
        super().__init__()
        self.console = console
        self.progress = Progress(
            SpinnerColumn(finished_text=":white_check_mark:"),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            TimeElapsedColumn(),
            console=self.console,
            transient=False,
        )
        self.current_task: Optional[TaskID] = None

    def handle_load_data(self, event: Event) -> None:
        if event.action_state == ActionState.Preceding:
            self.current_task = self.progress.add_task(
                "Load Data", start=True, total=None
            )

        if event.action_state == ActionState.Running:
            pass
        if event.action_state == ActionState.Done:
            if self.current_task is not None:
                self.progress.update(self.current_task, total=100, completed=100)

    def handle_pipeline(self, event: Event) -> None:
        self.current_task = None
        if event.action_state == ActionState.Preceding:
            self.progress.start()

    def handle_train(self, event: Event) -> None:
        if event.action_state == ActionState.Preceding:
            self.current_task = self.progress.add_task("Train", start=True, total=100)
            self.vdl_printed = False
            self.progress.log("Start training...")
        if event.action_state == ActionState.Running:
            if self.current_task is not None:
                resp = event.data
                self.progress.update(
                    self.current_task, completed=resp["result"]["progress"]
                )
                if not self.vdl_printed:
                    self.progress.log(
                        f"Training task id: {resp['result']['taskId']}, job id:"
                        f" {resp['result']['id']}, task name:"
                        f" {resp['result']['taskName']}"
                    )
                    self.progress.log(
                        "Check this vdl link to view training progress: "
                        + resp["result"]["vdlLink"]
                    )
                    self.vdl_printed = True
        if event.action_state == ActionState.Done:
            if self.current_task is not None:
                self.progress.update(self.current_task, completed=100)

    def handle_publish(self, event: Event) -> None:
        if event.action_state == ActionState.Preceding:
            self.current_task = self.progress.add_task(
                "Publish", start=True, total=None
            )
            self.progress.log("Start publishing model...")
        if event.action_state == ActionState.Running:
            pass
        if event.action_state == ActionState.Done:
            if self.current_task is not None:
                data = event.data
                self.progress.update(self.current_task, total=100, completed=100)
                self.progress.log(
                    "Model has been published successfully. Model id:"
                    f" {data['model_id']}. Model version id: {data['model_version_id']}"
                )

    def handle_deploy(self, event: Event) -> None:
        if event.action_state == ActionState.Preceding:
            self.current_task = self.progress.add_task("Deploy", start=True, total=None)
            self.progress.log("Start deploying service...")
        if event.action_state == ActionState.Running:
            pass
        if event.action_state == ActionState.Done:
            if self.current_task is not None:
                self.progress.update(self.current_task, total=100, completed=100)
                data = event.data
                self.progress.log(
                    "Service has been deployed successfully. Service id:"
                    f" {data['service_id']}. Service endpoint:"
                    f" {data['service_endpoint']}"
                )

    def handle_evaluate(self, event: Event) -> None:
        if event.action_state == ActionState.Preceding:
            self.current_task = self.progress.add_task(
                "Evaluate", start=True, total=None
            )
        if event.action_state == ActionState.Running:
            pass
        if event.action_state == ActionState.Done:
            if self.current_task is not None:
                self.progress.update(self.current_task, total=100, completed=100)

    def dispatch(self, event: Event) -> None:
        if event.action_state == ActionState.Stopped:
            print_error_msg(f"{event.action_class.__name__} {event.action_id} stopped.")
            return
        if event.action_state == ActionState.Error:
            self.console.log(
                "[bold red]ERROR[/bold red]:"
                f" {event.action_class.__name__} {event.action_id} failed with error:"
                f" {event.data}."
            )
            return
        handle_map: Dict[Any, Callable[[Event], None]] = {
            LoadDataSetAction: self.handle_load_data,
            TrainAction: self.handle_train,
            ModelPublishAction: self.handle_publish,
            DeployAction: self.handle_deploy,
            EvaluateAction: self.handle_evaluate,
            Pipeline: self.handle_pipeline,
        }
        handler = handle_map.get(event.action_class)
        if handler is None:
            raise InternalError(f"Unhandled event {event}")
        handler(event)


TRAIN_CONFIG_PANEL = "Train Config"
DEPLOY_CONFIG_PANEL = "Deploy Config"


@trainer_app.command()
@credential_required
def run(
    dataset_id: Optional[str] = typer.Option(None, help="Dataset id"),
    dataset_bos_path: Optional[str] = typer.Option(
        None,
        help="Dataset BOS path",
    ),
    train_type: str = typer.Option(..., help="Train type"),
    train_config_file: Optional[str] = typer.Option(
        None, help="Train config path, support \[json/yaml] "
    ),
    train_epoch: Optional[int] = typer.Option(
        None, help="Train epoch", rich_help_panel=TRAIN_CONFIG_PANEL
    ),
    train_batch_size: Optional[int] = typer.Option(
        None, help="Train batch size", rich_help_panel=TRAIN_CONFIG_PANEL
    ),
    train_learning_rate: Optional[float] = typer.Option(
        None, help="Train learning rate", rich_help_panel=TRAIN_CONFIG_PANEL
    ),
    train_max_seq_len: Optional[int] = typer.Option(
        None, help="Max sequence length", rich_help_panel=TRAIN_CONFIG_PANEL
    ),
    train_peft_type: Optional[PeftType] = typer.Option(
        None,
        help="Train peft type",
        **enum_typer(PeftType),
        rich_help_panel=TRAIN_CONFIG_PANEL,
    ),
    trainset_rate: int = typer.Option(
        20, help="Trainset ratio", rich_help_panel=TRAIN_CONFIG_PANEL
    ),
    train_logging_steps: Optional[int] = typer.Option(
        None, help="Logging steps", rich_help_panel=TRAIN_CONFIG_PANEL
    ),
    train_warmup_ratio: Optional[float] = typer.Option(
        None, help="Warmup ratio", rich_help_panel=TRAIN_CONFIG_PANEL
    ),
    train_weight_decay: Optional[float] = typer.Option(
        None, help="Weight decay", rich_help_panel=TRAIN_CONFIG_PANEL
    ),
    train_lora_rank: Optional[int] = typer.Option(
        None, help="Lora rank", rich_help_panel=TRAIN_CONFIG_PANEL
    ),
    train_lora_all_linear: Optional[str] = typer.Option(
        None,
        help="Whether lora is all linear layer",
        rich_help_panel=TRAIN_CONFIG_PANEL,
    ),
    deploy_name: Optional[str] = typer.Option(
        None,
        help="Deploy name. Set this value to enable deploy action.",
        rich_help_panel=DEPLOY_CONFIG_PANEL,
    ),
    deploy_endpoint_prefix: Optional[str] = typer.Option(
        None, help="Deploy endpoint prefix", rich_help_panel=DEPLOY_CONFIG_PANEL
    ),
    deploy_description: str = typer.Option(
        "", help="Deploy description", rich_help_panel=DEPLOY_CONFIG_PANEL
    ),
    deploy_replicas: int = typer.Option(
        1, help="Deploy replicas", rich_help_panel=DEPLOY_CONFIG_PANEL
    ),
    deploy_pool_type: str = typer.Option(
        "private_resource",
        help="Deploy pool type",
        **enum_typer(DeployPoolType),
        rich_help_panel=DEPLOY_CONFIG_PANEL,
    ),
    deploy_service_type: str = typer.Option(
        "chat",
        help="Service Type",
        **enum_typer(ServiceType),
        rich_help_panel=DEPLOY_CONFIG_PANEL,
    ),
) -> None:
    """
    Run a trainer job.
    """
    console = replace_logger_handler()
    callback = MyEventHandler(console=console)
    ds = None
    if dataset_id is not None:
        ds = Dataset.load(
            qianfan_dataset_id=dataset_id, is_download_to_local=False, does_release=True
        )
    deploy_config = None
    if deploy_name is not None:
        if deploy_endpoint_prefix is None:
            print_error_msg("Deploy endpoint prefix is required")
            raise typer.Exit(code=1)

        deploy_config = DeployConfig(
            name=deploy_name,
            endpoint_prefix=deploy_endpoint_prefix,
            description=deploy_description,
            replicas=deploy_replicas,
            pool_type=DeployPoolType[deploy_pool_type],
            service_type=ServiceType[deploy_service_type],
        )

    trainer = LLMFinetune(
        dataset=ds,
        train_type=train_type,
        event_handler=callback,
        train_config=train_config_file,
        deploy_config=deploy_config,
        dataset_bos_path=dataset_bos_path,
    )

    if trainer.train_action.train_config is None:
        raise InternalError("Train config not found in trainer.")

    if train_epoch is not None:
        trainer.train_action.train_config.epoch = train_epoch
    if train_batch_size is not None:
        trainer.train_action.train_config.batch_size = train_batch_size
    if train_learning_rate is not None:
        trainer.train_action.train_config.learning_rate = train_learning_rate
    if train_max_seq_len is not None:
        trainer.train_action.train_config.max_seq_len = train_max_seq_len
    if train_peft_type is not None:
        trainer.train_action.train_config.peft_type = train_peft_type
    if trainset_rate is not None:
        trainer.train_action.train_config.trainset_rate = trainset_rate
    if train_logging_steps is not None:
        trainer.train_action.train_config.logging_steps = train_logging_steps
    if train_warmup_ratio is not None:
        trainer.train_action.train_config.warmup_ratio = train_warmup_ratio
    if train_weight_decay is not None:
        trainer.train_action.train_config.weight_decay = train_weight_decay
    if train_lora_rank is not None:
        trainer.train_action.train_config.lora_rank = train_lora_rank
    if train_lora_all_linear is not None:
        trainer.train_action.train_config.lora_all_linear = train_lora_all_linear

    trainer.run()

    console.log("Trainer finished!")

    # wait a second for the log to be flushed
    time.sleep(0.1)
