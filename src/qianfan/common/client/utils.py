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

from datetime import datetime
from typing import Any, Dict, Optional, Type, TypeVar

import typer
from rich import print as rprint

import qianfan
from qianfan.resources.llm.base import BaseResource

BaseResourceType = TypeVar("BaseResourceType", bound=BaseResource)
command_to_resource_type: Dict[str, Type[BaseResource]] = {
    "chat": qianfan.ChatCompletion,
    "txt2img": qianfan.Text2Image,
    "completion": qianfan.Completion,
    "embedding": qianfan.Embedding,
}


def print_error_msg(msg: str) -> None:
    """
    Print an error message in the console.
    """
    rprint(f"[bold red]ERROR[/bold red]: {msg}")


def print_warn_msg(msg: str) -> None:
    """
    Print a warning message in the console.
    """
    rprint(f"[bold orange1]WARN[/bold orange1]: {msg}")


def create_client(
    type: Type[BaseResourceType], model: str, endpoint: Optional[str], **kwargs: Any
) -> BaseResourceType:
    """
    Create the client according to the type, model and endpoint.
    """
    if endpoint is not None:
        return type(endpoint=endpoint, **kwargs)
    else:
        return type(model=model, **kwargs)


def timestamp(time: datetime = datetime.now()) -> str:
    """
    Return a timestamp string used in the client.
    """
    return time.strftime("%Y%m%d_%H%M%S")


def list_model_callback(
    ctx: typer.Context, param: typer.CallbackParam, value: bool
) -> None:
    """
    Print models of ChatCompletion and exit.
    """
    if value:
        cmd = ctx.command
        if cmd.name is None:
            print_error_msg("No command is specified.")
            raise typer.Exit(1)
        t = command_to_resource_type[cmd.name]
        models = t.models()
        for m in sorted(models):
            print(m)
        raise typer.Exit()


list_model_option = typer.Option(
    None,
    "--list-model",
    "-l",
    callback=list_model_callback,
    is_eager=True,
    help="Print supported models.",
)
