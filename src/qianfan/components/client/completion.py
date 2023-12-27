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

import typer
from rich import print

import qianfan
from qianfan import Messages, QfRole
from qianfan.components.client.utils import create_client, print_error_msg


def completion_single(message: str, client: qianfan.Completion) -> None:
    res = client.do(prompt=message)
    print(res["result"])


def completion_multi(messages: List[str], client: qianfan.ChatCompletion) -> None:
    msg_history = Messages()
    for i, message in enumerate(messages):
        if i % 2 == 0:
            msg_history.append(message, role=QfRole.User)
        else:
            msg_history.append(message, role=QfRole.Assistant)
    res = client.do(messages=msg_history)
    print(res["result"])


def completion_entry(
    messages: List[str] = typer.Argument(..., help="Messages"),
    model: str = typer.Option("ERNIE-Bot-turbo", help="Model name"),
    endpoint: Optional[str] = typer.Option(None, help="Endpoint"),
):
    if len(messages) % 2 != 1:
        print_error_msg("The number of messages must be odd.")
        raise typer.Exit(code=1)
    if len(messages) == 1:
        client = create_client(qianfan.Completion, model, endpoint)
        completion_single(messages[0], client)
    else:
        client = create_client(qianfan.ChatCompletion, model, endpoint)
        completion_multi(messages, client)
