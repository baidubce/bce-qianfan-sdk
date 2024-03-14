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
from typing import Any, Callable, Dict, List, Optional

import typer
from rich.console import Console
from rich.pretty import Pretty
from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TaskID,
    TaskProgressColumn,
    TextColumn,
    TimeElapsedColumn,
)
from rich.table import Table

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
from qianfan.resources.console.consts import DeployPoolType, FinetuneSupportModelType
from qianfan.trainer import LLMFinetune, PostPreTrain
from qianfan.trainer.actions import (
    DeployAction,
    EvaluateAction,
    LoadDataSetAction,
    ModelPublishAction,
    TrainAction,
)
from qianfan.trainer.base import Pipeline
from qianfan.trainer.configs import ModelInfo, TrainLimit
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
            if self.current_task is None:
                return
            resp = event.data
            result = resp["result"]
            status = result["runStatus"]
            if status == "Running":
                progress = int(result["runProgress"][:-1])
                self.progress.update(self.current_task, completed=progress)
            elif status == "Failed":
                self.progress.log("Task failed.")
                return
            elif status == "Stopped":
                self.progress.log("Task stopped.")
                return

            if not self.vdl_printed:
                self.progress.log(
                    f"{result['trainMode']} task id: {resp['result']['taskId']}, job"
                    f" id: {resp['result']['jobId']}, jobName:"
                    f" {resp['result']['jobName']}"
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


def list_train_type(
    ctx: typer.Context, param: typer.CallbackParam, value: bool
) -> None:
    """
    list all the supported train types
    """
    if value:
        console = replace_logger_handler()
        cmd = ctx.command.name
        if cmd is None:
            print_error_msg(
                "Command name is not specified. Might be an internal error."
            )
            raise typer.Exit(1)
        if cmd == "postpretrain":
            model_list = PostPreTrain.train_type_list()
        elif cmd in ["finetune", "run"]:
            model_list = LLMFinetune.train_type_list()
        else:
            print_error_msg(
                f"Command {cmd} is not supported. Might be an internal error."
            )
            raise typer.Exit(1)

        model_type_map: Dict[FinetuneSupportModelType, Dict[str, List]] = {}
        for model, info in model_list.items():
            if info.model_type not in model_type_map:
                model_type_map[info.model_type] = {}
            if info.base_model_type not in model_type_map[info.model_type]:
                model_type_map[info.model_type][info.base_model_type] = []
            model_type_map[info.model_type][info.base_model_type].append(model)

        for type, model_set in model_type_map.items():
            console.print(f"[bold red]{type.name}:[/]")
            for base_model, models in model_set.items():
                console.print(f"  [bold green]{base_model}:[/]")
                for model in sorted(models):
                    info = model_list[model]
                    if info.deprecated:
                        console.print(
                            f"    [s]{model}[dim] (deprecated)[/]", highlight=False
                        )
                    else:
                        console.print(f"    {model}", highlight=False)

        raise typer.Exit()


def print_trainer_config(config: ModelInfo) -> None:
    """
    Print trainer config
    """
    table = Table()
    table.add_column("")
    for p in config.support_peft_types:
        table.add_column(Pretty(p.value, overflow="fold"))
    from qianfan.trainer.configs import TrainConfig

    limit_fields = (
        TrainConfig().dict(exclude={"peft_type", "trainset_rate", "extras"}).keys()
    )
    for k in limit_fields:
        row_objs = []
        row_objs.append(k)
        has_not_none_limit = False
        for peft in config.support_peft_types:
            peft_limit: Optional[TrainLimit] = config.common_params_limit
            if config.specific_peft_types_params_limit:
                specific_train_limit = config.specific_peft_types_params_limit.get(peft)
                if specific_train_limit is not None:
                    peft_limit = specific_train_limit | config.common_params_limit
            if peft_limit and peft_limit.get(k):
                row_objs.append(f"{peft_limit.get(k)}")
                has_not_none_limit = True
            else:
                row_objs.append("---")
        if has_not_none_limit:
            table.add_row(*[a for a in row_objs])
    Console().print(table)


def show_config_limit(
    ctx: typer.Context, param: typer.CallbackParam, value: str
) -> None:
    """
    show config limit for specified train type
    """
    if value:
        cmd = ctx.command.name
        if cmd is None:
            print_error_msg(
                "Command name is not specified. Might be an internal error."
            )
            raise typer.Exit(1)
        if cmd == "postpretrain":
            model_list = PostPreTrain.train_type_list()
        elif cmd in ["finetune", "run"]:
            model_list = LLMFinetune.train_type_list()
        else:
            print_error_msg(
                f"Command {cmd} is not supported. Might be an internal error."
            )
            raise typer.Exit(1)

        if value not in model_list:
            print_error_msg(f"Train type {value} is not supported.")
            raise typer.Exit(1)
        print_trainer_config(model_list[value])
        raise typer.Exit()


list_train_type_option = typer.Option(
    None,
    "--list-train-type",
    "-l",
    callback=list_train_type,
    is_eager=True,
    help="Print supported train types.",
)


@trainer_app.command(
    "run",
    deprecated=True,
    help=(
        "Run a finetune trainer task. This command is deprecated and use command"
        " `finetune` instead."
    ),
)
@trainer_app.command()
@credential_required
def finetune(
    dataset_id: Optional[str] = typer.Option(None, help="Dataset id"),
    dataset_bos_path: Optional[str] = typer.Option(
        None,
        help="Dataset BOS path",
    ),
    train_type: str = typer.Option(..., help="Train type"),
    previous_task_id: Optional[str] = typer.Option(
        None, help="Task id of previous trainer output."
    ),
    list_train_type: Optional[bool] = list_train_type_option,
    show_config_limit: Optional[str] = typer.Option(
        None,
        callback=show_config_limit,
        is_eager=True,
        help="Show config limit for specified train type.",
    ),
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
    Run a finetune trainer job.
    """
    console = replace_logger_handler()
    callback = MyEventHandler(console=console)
    ds = None
    if dataset_id is not None:
        ds = Dataset.load(qianfan_dataset_id=dataset_id, does_release=True)
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
        previous_task_id=previous_task_id,
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
    console.log(Pretty(trainer.output))

    # wait a second for the log to be flushed
    time.sleep(0.1)


@trainer_app.command()
@credential_required
def postpretrain(
    dataset_id: Optional[str] = typer.Option(None, help="Dataset id"),
    dataset_bos_path: Optional[str] = typer.Option(
        None,
        help="Dataset BOS path",
    ),
    train_type: str = typer.Option(..., help="Train type"),
    list_train_type: Optional[bool] = list_train_type_option,
    show_config_limit: Optional[str] = typer.Option(
        None,
        callback=show_config_limit,
        is_eager=True,
        help="Show config limit for specified train type.",
    ),
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
    Run a postpretrain trainer job.
    """
    console = replace_logger_handler()
    callback = MyEventHandler(console=console)
    ds = None
    if dataset_id is not None:
        ds = Dataset.load(qianfan_dataset_id=dataset_id, does_release=True)
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

    trainer = PostPreTrain(
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
    console.log(Pretty(trainer.output))

    # wait a second for the log to be flushed
    time.sleep(0.1)
