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
from qianfan.trainer.configs import TrainConfig
from qianfan.trainer.event import Event, EventHandler
from qianfan.trainer.consts import ActionState
from qianfan.common.client.dataset import load_dataset

trainer_app = typer.Typer(no_args_is_help=True)


@trainer_app.command()
def run(
    dataset: str = typer.Option(..., help="Dataset name"),
    train_type: str = typer.Option(..., help="Train type"),
):
    """
    Run a trainer job.
    """
    import qianfan

    qianfan.enable_log("INFO")
    ds = load_dataset(dataset)
    trainer = LLMFinetune(
        dataset=ds,
        train_type=train_type,
    )
    trainer.run()
