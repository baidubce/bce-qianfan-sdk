# Copyright (c) 2024 Baidu, Inc. All Rights Reserved.
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

import json
import time

import typer

from qianfan import resources
from qianfan.common.cli.utils import (
    credential_required,
)
from qianfan.resources.console.utils import call_action

api_app = typer.Typer(
    no_args_is_help=True,
    help="Qianfan api",
    context_settings={"help_option_names": ["-h", "--help"]},
)


@api_app.command(name="finetune.task.detail")
@credential_required
def task_info(
    task_id: str = typer.Option(..., help="task id"),
) -> None:
    """
    get a finetune task info from local cache
    """
    resp = resources.FineTune.V2.task_detail(task_id=task_id)
    json_str = json.dumps(resp.body, ensure_ascii=False, indent=2)
    print(json_str)

    # wait a second for the log to be flushed
    time.sleep(0.1)


@api_app.command(name="raw.console")
@credential_required
def call_console(
    route: str = typer.Option(..., help="route, e.g. /v2/finetuning"),
    action: str = typer.Option(..., help="action, e.g. DescribeFineTuningTask"),
    data: str = typer.Option(..., help="req body"),
) -> None:
    """
    create a console action api call
    """
    d = json.loads(data)
    assert isinstance(d, dict)
    resp = call_action(base_url_route=route, action=action, params=d)
    json_str = json.dumps(resp.body, ensure_ascii=False, indent=2)
    print(json_str)

    # wait a second for the log to be flushed
    time.sleep(0.1)
