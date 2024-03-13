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

import json
from datetime import datetime
from enum import Enum
from functools import wraps
from http import HTTPStatus
from typing import Any, Callable, Dict, List, Optional, Type, TypeVar

import click
import typer
from prompt_toolkit import prompt
from prompt_toolkit.document import Document
from prompt_toolkit.validation import ValidationError, Validator
from rich import print as rprint
from rich.console import Console, Group, RenderableType
from rich.highlighter import JSONHighlighter
from rich.logging import RichHandler
from rich.panel import Panel
from rich.text import Text

import qianfan
import qianfan.utils.logging as qianfan_logging
from qianfan import QfResponse
from qianfan.resources.llm.base import BaseResource
from qianfan.resources.typing import QfRequest
from qianfan.utils.bos_uploader import BosHelper, parse_bos_path
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
    bos_helper = BosHelper()
    region = bos_helper.get_bos_bucket_location(bucket)
    return region


def list_model_callback(
    ctx: typer.Context, param: typer.CallbackParam, value: bool
) -> None:
    """
    Print models of ChatCompletion and exit.
    """
    if value:
        console = replace_logger_handler()
        cmd = ctx.command
        if cmd.name is None:
            print_error_msg("No command is specified.")
            raise typer.Exit(1)
        t = command_to_resource_type[cmd.name]
        models = t.models()
        for m in sorted(models):
            info = t.get_model_info(m)
            if info.depracated:
                console.print(f"[s]{m} [dim](depracated)[/]", highlight=False)
            else:
                console.print(m, highlight=False)
        raise typer.Exit()


def replace_logger_handler(**kwargs: Any) -> Console:
    console = Console(log_time_format="[%m/%d/%y %H:%M:%S]", **kwargs)
    logger = qianfan_logging.logger._logger
    handlers = logger.handlers
    for handler in handlers:
        logger.removeHandler(handler)
    logger.addHandler(RichHandler(console=console))
    return console


def check_credential() -> None:
    ak = qianfan.get_config().AK
    sk = qianfan.get_config().SK
    access_key = qianfan.get_config().ACCESS_KEY
    secret_key = qianfan.get_config().SECRET_KEY

    if ak is None or sk is None:
        if access_key is None or secret_key is None:
            print_info_msg(
                'No enough credential found. Please provide your "access key" and'
                ' "secret key".'
            )
            print_info_msg(
                "You can find your key at"
                " https://console.bce.baidu.com/iam/#/iam/accesslist"
            )
            print_info_msg(
                "You can also set the credential using environment variable"
                ' "QIANFAN_ACCESS_KEY" and "QIANFAN_SECRET_KEY".'
            )
            print()
            if access_key is None:
                while True:
                    rprint("Please input your [b i]Access Key[/b i]: ", end="")
                    access_key = prompt()
                    if len(access_key) != 0:
                        qianfan.get_config().ACCESS_KEY = access_key
                        break
                    else:
                        print_error_msg("Access key cannot be empty.")
            if secret_key is None:
                while True:
                    rprint("Please input your [b i]Secret Key[/b i]: ", end="")
                    secret_key = prompt()
                    if len(secret_key) != 0:
                        qianfan.get_config().SECRET_KEY = secret_key
                        break
                    else:
                        print_error_msg("Secret key cannot be empty.")
            print()


def credential_required(func: Callable) -> Callable:
    """
    Check the credential is provided.
    """

    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        check_credential()
        return func(*args, **kwargs)

    return wrapper


list_model_option = typer.Option(
    None,
    "--list-model",
    "-l",
    callback=list_model_callback,
    is_eager=True,
    help="Print supported models.",
)


def _render_request_body(headers: Dict[str, str], body: Any) -> Group:
    header_list: List[RenderableType] = []
    for k, v in headers.items():
        header_list.append(Text.from_markup(f"[red]{k}[/]: {v}"))
    header_list.append(Text.from_markup(""))
    body_obj = Text.from_markup(json.dumps(body, indent=4, ensure_ascii=False))
    JSONHighlighter().highlight(body_obj)
    header_list.append(body_obj)
    return Group(*header_list)


def _render_request(request: QfRequest) -> Group:
    render_list: List[RenderableType] = []
    render_list.append(Text.from_markup(f"[magenta]{request.method}[/] {request.url}"))
    render_list.append(_render_request_body(request.headers, request.json_body))
    return Group(*render_list)


def _render_response(response: QfResponse) -> Group:
    render_list: List[RenderableType] = []
    render_list.append(
        Text.from_markup(
            f"[yellow]{response.code}[/] {HTTPStatus(response.code).phrase}"
        )
    )
    render_list.append(_render_request_body(response.headers, response.body))
    content_type = response.headers.get("Content-Type")
    if content_type is not None and "event-stream" in content_type:
        render_list.append(
            Text.from_markup(
                "\n[dim](Since streaming output is enabled, only the last response is"
                " printed.)[/]"
            )
        )
    return Group(*render_list)


def render_response_debug_info(response: QfResponse) -> Group:
    request = response.request
    render_list: List[RenderableType] = []
    if request is not None:
        render_list.append(
            Panel(
                _render_request(request),
                title="[cyan]Request[/] [dim](for debug)[/]",
                title_align="left",
            )
        )
    render_list.append(
        Panel(
            _render_response(response),
            title="[cyan]Response[/] [dim](for debug)[/]",
            title_align="left",
        )
    )

    return Group(*render_list)


class InputEmptyValidator(Validator):
    def validate(self, document: Document) -> None:
        text = document.text
        if len(text.strip()) == 0:
            raise ValidationError(message="Input cannot be empty")


class BosPathValidator(Validator):
    def validate(self, document: Document) -> None:
        text = document.text.strip()
        if len(text) == 0:
            raise ValidationError(message="Input cannot be empty")
        try:
            parse_bos_path("bos:/" + text)
        except ValueError:
            raise ValidationError(message="Invalid BOS path")
