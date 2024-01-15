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
from enum import Enum
from typing import Any, Dict, Optional, Type, TypeVar

import click
import typer
from rich import print as rprint
from rich.console import Console
from rich.logging import RichHandler

import qianfan
import qianfan.utils.logging as qianfan_logging
from qianfan.resources.llm.base import BaseResource
from qianfan.utils.bos_uploader import get_bos_bucket_location
from qianfan.utils.utils import camel_to_snake, snake_to_camel

BaseResourceType = TypeVar("BaseResourceType", bound=BaseResource)
command_to_resource_type: Dict[str, Type[BaseResource]] = {
    "chat": qianfan.ChatCompletion,
    "txt2img": qianfan.Text2Image,
    "completion": qianfan.Completion,
    "embedding": qianfan.Embedding,
}


def print_error_msg(msg: str, exit: bool = False) -> None:
    """
    Print an error message in the console.
    """
    rprint(f"[bold red]ERROR[/bold red]: {msg}")
    if exit:
        raise typer.Exit(1)


def print_warn_msg(msg: str) -> None:
    """
    Print a warning message in the console.
    """
    rprint(f"[bold orange1]WARN[/bold orange1]: {msg}")


def print_info_msg(msg: str) -> None:
    """
    Print an info message in the console.
    """
    rprint(f"[bold]INFO[/bold]: {msg}")


def print_success_msg(msg: str) -> None:
    """
    Print a success message in the console.
    """
    rprint(f"[bold green]SUCCESS[/bold green]: {msg}")


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


def enum_list(enum_type: Type[Enum]) -> list:
    """
    Return a list of the enum values.
    """
    members = enum_type.__members__.keys()
    return [camel_to_snake(member) for member in members]


def enum_typer(enum_type: Type[Enum]) -> Dict[str, Any]:
    return {"click_type": click.Choice(enum_list(enum_type)), "callback": enum_callback}


def enum_callback(ctx: typer.Context, param: typer.CallbackParam, value: str) -> Any:
    """
    update qianfan config
    """
    if value is not None and len(value.strip()) > 0:
        return snake_to_camel(value)


def assert_not_none(value: Any, var_name: str) -> None:
    """
    Assert the value is not none.
    """
    if not value:
        print_error_msg(f"{var_name} is required.")
        raise typer.Exit(1)


def bos_bucket_region(bucket: str) -> str:
    """
    Get the bos bucket location.
    """
    global_config = qianfan.get_config()
    if global_config.ACCESS_KEY is None or global_config.SECRET_KEY is None:
        print_error_msg("ACCESS_KEY and SECRET_KEY are required.")
        raise typer.Exit(1)
    region = get_bos_bucket_location(
        bucket,
        global_config.BOS_HOST_REGION,
        global_config.ACCESS_KEY,
        global_config.SECRET_KEY,
    )
    return region


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


def replace_logger_handler() -> Console:
    console = Console(log_time_format="[%m/%d/%y %H:%M:%S]")
    logger = qianfan_logging.logger._logger
    handlers = logger.handlers
    for handler in handlers:
        logger.removeHandler(handler)
    logger.addHandler(RichHandler(console=console))
    return console


list_model_option = typer.Option(
    None,
    "--list-model",
    "-l",
    callback=list_model_callback,
    is_eager=True,
    help="Print supported models.",
)
