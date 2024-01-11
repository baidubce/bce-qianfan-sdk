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

from typing import List, Optional

import prompt_toolkit
import typer
from rich import print as rprint
from rich.console import Console
from rich.markdown import Markdown

import qianfan
from qianfan import Messages, QfResponse, QfRole
from qianfan.common.client.utils import (
    create_client,
    list_model_option,
    print_error_msg,
    print_info_msg,
)
from qianfan.consts import DefaultLLMModel


class CompletionClient(object):
    """
    Client class for completion command.
    """

    def __init__(self, model: str, endpoint: Optional[str], plain: bool):
        """
        Init the client.
        """
        self.model = model
        self.endpoint = endpoint
        self.plain = plain
        self.console = Console()

    def completion_single(self, message: str) -> None:
        """
        Use Completion to complete the given message.
        """
        client = create_client(qianfan.Completion, self.model, self.endpoint)

        if self.plain:
            res = client.do(prompt=message)
            assert isinstance(res, QfResponse)
            print(res["result"])
        else:
            with self.console.status("Generating"):
                res = client.do(prompt=message)
            assert isinstance(res, QfResponse)
            rprint(Markdown(res["result"]))

    def completion_multi(self, messages: List[str]) -> None:
        """
        Use ChatCompletion to complete the given messages.
        """
        msg_history = Messages()
        for i, message in enumerate(messages):
            if i % 2 == 0:
                msg_history.append(message, role=QfRole.User)
            else:
                msg_history.append(message, role=QfRole.Assistant)
        client = create_client(qianfan.ChatCompletion, self.model, self.endpoint)

        if self.plain:
            res = client.do(messages=msg_history)
            assert isinstance(res, QfResponse)
            print(res["result"])
        else:
            with self.console.status("Generating"):
                res = client.do(messages=msg_history)
            assert isinstance(res, QfResponse)
            rprint(Markdown(res["result"]))


def completion_entry(
    prompts: Optional[List[str]] = typer.Argument(None, help="Prompt List"),
    model: str = typer.Option(
        DefaultLLMModel.Completion,
        help="Model name of the completion model.",
        autocompletion=qianfan.Completion.models,
    ),
    endpoint: Optional[str] = typer.Option(
        None,
        help=(
            "Endpoint of the completion model. This option will override `model`"
            " option."
        ),
    ),
    plain: bool = typer.Option(False, help="Plain text mode won't use rich text"),
    list_model: bool = list_model_option,
    multi_line: bool = typer.Option(
        False,
        "--multi-line",
        help="Multi-line mode which needs to press Esc before enter to submit message.",
    ),
) -> None:
    """
    Complete the provided prompt or messages.
    """
    if prompts is None or len(prompts) == 0:
        if multi_line:
            print_info_msg(
                "Multi-line mode is enabled. [green bold]Press Esc before Enter[/] to"
                " submit prompt.\n"
            )
        while True:
            print("Please enter your prompt:")
            prompt = prompt_toolkit.prompt(multiline=multi_line).strip()
            if len(prompt) != 0:
                prompts = [prompt]
                break
            print_error_msg("Prompt can't be empty.\n")

    if len(prompts) % 2 != 1:
        print_error_msg("The number of messages must be odd.")
        raise typer.Exit(code=1)
    client = CompletionClient(model, endpoint, plain)

    if len(prompts) == 1:
        client.completion_single(prompts[0])
    else:
        client.completion_multi(prompts)
