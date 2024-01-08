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


import re
from pathlib import Path
from typing import Any, Optional

import typer
from rich.console import Console, Group
from rich.pretty import Pretty
from rich.rule import Rule
from rich.table import Table
import qianfan
from qianfan.errors import InternalError

import qianfan.common.client.utils as client_utils
from qianfan.common.client.utils import (
    enum_typer,
    print_error_msg,
    print_info_msg,
    replace_logger_handler,
    timestamp,
)

from qianfan.model.consts import ServiceType
from qianfan.resources.console.consts import DeployPoolType
from qianfan.consts import DefaultLLMModel
from qianfan.dataset import Dataset, DataStorageType, DataTemplateType
from qianfan.dataset.data_source import QianfanDataSource
from qianfan.utils.bos_uploader import parse_bos_path
from qianfan.trainer import LLMFinetune
from qianfan.trainer.base import Pipeline
from qianfan.trainer.configs import TrainConfig
from qianfan.trainer.event import Event, EventHandler
from qianfan.trainer.actions import (
    DeployAction,
    EvaluateAction,
    LoadDataSetAction,
    TrainAction,
    ModelPublishAction,
)
from qianfan.model.configs import DeployConfig
from qianfan.trainer.consts import ActionState, PeftType
from qianfan.common.client.dataset import load_dataset
from rich.progress import Progress, SpinnerColumn, TimeElapsedColumn
from qianfan.utils.logging import log_info, log_error

trainer_app = typer.Typer(no_args_is_help=True)


class MyEventHandler(EventHandler):
    def __init__(self, console) -> None:
        super().__init__()
        self.console = console
        self.progress = Progress(
            SpinnerColumn(finished_text=":white_check_mark:"),
            *Progress.get_default_columns(),
            TimeElapsedColumn(),
            console=self.console,
            transient=False,
        )
        self.current_task = None

    def handle_load_data(self, event: Event) -> None:
        if event.action_state == ActionState.Preceding:
            self.current_task = self.progress.add_task(
                "Load Data", start=True, total=None
            )

        if event.action_state == ActionState.Running:
            pass
        if event.action_state == ActionState.Done:
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
            resp = event.data
            self.progress.update(
                self.current_task, completed=resp["result"]["progress"]
            )
            if not self.vdl_printed:
                self.progress.log(
                    f"Training task id: {resp['result']['taskId']}, job id:"
                    f" {resp['result']['id']}, task name: {resp['result']['taskName']}"
                )
                self.progress.log(
                    "Check this vdl link to view training progress: "
                    + resp["result"]["vdlLink"]
                )
                self.vdl_printed = True
        if event.action_state == ActionState.Done:
            resp = event.data
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
            data = event.data
            self.progress.update(self.current_task, total=100, completed=100)
            self.progress.log(
                f"Model has been published successfully. Model id: {data['model_id']}."
                f" Model version id: {data['model_version_id']}"
            )

    def handle_deploy(self, event: Event) -> None:
        if event.action_state == ActionState.Preceding:
            self.current_task = self.progress.add_task("Deploy", start=True, total=None)
            self.progress.log("Start deploying service...")
        if event.action_state == ActionState.Running:
            pass
        if event.action_state == ActionState.Done:
            self.progress.update(self.current_task, total=100, completed=100)
            data = event.data
            self.progress.log(
                "Service has been deployed successfully. Service id:"
                f" {data['service_id']}. Service endpoint: {data['service_endpoint']}"
            )

    def handle_evaluate(self, event: Event) -> None:
        if event.action_state == ActionState.Preceding:
            self.current_task = self.progress.add_task(
                "Evaluate", start=True, total=None
            )
        if event.action_state == ActionState.Running:
            pass
        if event.action_state == ActionState.Done:
            self.progress.update(self.current_task, total=100, completed=100)

    def dispatch(self, event: Event) -> None:
        # self.progress.log(str(event))
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
        handle_map = {
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


@trainer_app.command()
def run(
    dataset_id: int = typer.Option(..., help="Dataset name"),
    train_type: str = typer.Option(..., help="Train type"),
):
    """
    Run a trainer job.
    """
    # qianfan.enable_log("INFO")
    console = replace_logger_handler()
    callback = MyEventHandler(console=console)
    ds = Dataset.load(qianfan_dataset_id=dataset_id)
    trainer = LLMFinetune(
        dataset=ds,
        train_type=train_type,
        event_handler=callback,
        train_config=TrainConfig(
            batch_size=1, epoch=1, learning_rate=0.00002, peft_type=PeftType.ALL
        ),
        deploy_config=DeployConfig(
            name="sdkcqasvc",
            endpoint_prefix="sdkcqa1",
            replicas=1,  # 副本数， 与qps强绑定
            pool_type=DeployPoolType.PrivateResource,  # 私有资源池
            service_type=ServiceType.Chat,
        ),
    )
    trainer.run()
    console.log("Trainer finished!")
    import time

    time.sleep(0.1)
