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
from qianfan.errors import InternalError

import qianfan.common.client.utils as client_utils
from qianfan.common.client.utils import (
    enum_typer,
    print_error_msg,
    print_info_msg,
    print_success_msg,
    timestamp,
)
from qianfan.consts import DefaultLLMModel
from qianfan.dataset import Dataset, DataStorageType, DataTemplateType
from qianfan.dataset.data_source import QianfanDataSource
from qianfan.utils.bos_uploader import parse_bos_path
from qianfan.trainer import LLMFinetune
from qianfan.trainer.base import Pipeline
from qianfan.trainer.configs import TrainConfig
from qianfan.trainer.event import Event, EventHandler
from qianfan.trainer.actions import LoadDataSetAction, TrainAction, ModelPublishAction
from qianfan.trainer.consts import ActionState, PeftType
from qianfan.common.client.dataset import load_dataset
from rich.progress import Progress, SpinnerColumn, TimeElapsedColumn


trainer_app = typer.Typer(no_args_is_help=True)


class MyEventHandler(EventHandler):
    def __init__(self) -> None:
        super().__init__()
        self.console = Console()
        self.progress = Progress(
            SpinnerColumn(finished_text=":white_check_mark:"),
            *Progress.get_default_columns(),
            TimeElapsedColumn(),
            console=self.console,
            transient=False,
        )
        self.load_data_task = self.progress.add_task(
            "Load data", total=100, start=False, visible=False
        )
        self.train_task = self.progress.add_task(
            "Train", total=100, start=False, visible=False
        )
        self.publish_task = self.progress.add_task(
            "Publish", total=100, start=False, visible=False
        )
        self.current_task = None
        self.vdl_printed = False

    def handle_load_data(self, event: Event) -> None:
        if self.current_task is None:
            self.current_task = "load_data"
            self.progress.start_task(self.load_data_task)
            self.progress.update(self.load_data_task, visible=True)
        if (
            event.action_state == ActionState.Preceding
            or event.action_state == ActionState.Running
        ):
            pass
        if event.action_state == ActionState.Done:
            self.progress.update(self.load_data_task, completed=100)

    def handle_pipeline(self, event: Event) -> None:
        self.current_task = None
        if event.action_state == ActionState.Preceding:
            self.progress.start()
        pass

    def handle_train(self, event: Event) -> None:
        if self.current_task is None:
            self.current_task = "train"
            self.progress.start_task(self.train_task)
            self.progress.update(self.train_task, visible=True)
        if event.action_state == ActionState.Running:
            resp = event.data
            self.progress.update(self.train_task, completed=resp["result"]["progress"])
            if not self.vdl_printed:
                self.progress.log("vdl link: " + resp["result"]["vdlLink"])
                self.vdl_printed = True
        if event.action_state == ActionState.Done:
            resp = event.data
            self.progress.update(self.train_task, completed=100)

    def handle_publish(self, event: Event) -> None:
        if self.current_task is None:
            self.current_task = "publish_model"
            self.progress.start_task(self.publish_task)
            self.progress.update(self.publish_task, visible=True)
        if (
            event.action_state == ActionState.Preceding
            or event.action_state == ActionState.Running
        ):
            pass
        if event.action_state == ActionState.Done:
            self.progress.update(self.load_data_task, completed=100)

    def dispatch(self, event: Event) -> None:
        self.progress.log(str(event))
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
    callback = MyEventHandler()
    ds = Dataset.load(qianfan_dataset_id=dataset_id)
    trainer = LLMFinetune(
        dataset=ds,
        train_type=train_type,
        event_handler=callback,
        train_config=TrainConfig(
            batch_size=1, epoch=1, learning_rate=0.00002, peft_type=PeftType.ALL
        ),
    )
    trainer.run()
