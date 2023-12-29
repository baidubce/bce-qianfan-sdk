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

from typing import Optional

import typer
from rich import print as rprint
from rich.console import Console
from rich.live import Live
from rich.markdown import Markdown

import qianfan
from qianfan import Messages, QfRole
from qianfan.common.client.utils import (
    create_client,
    list_model_option,
    print_error_msg,
)
from qianfan.consts import DefaultLLMModel

END_PROMPT = "\exit"


class ChatClient(object):
    """
    Client object for the chat command
    """

    def __init__(self, model: str, endpoint: Optional[str], multi_line: bool) -> None:
        """
        Init the chat client
        """
        self.client = create_client(qianfan.ChatCompletion, model, endpoint)
        self.multi_line = multi_line
        self.console = Console()

    def chat_in_terminal(self) -> None:
        """
        Chat in terminal
        """
        messages = Messages()
        if self.multi_line:
            rprint(
                "[bold]Hint[/bold]: Press enter [bold]twice[/bold] to submit your"
                f" message, and use '{END_PROMPT}' to end the conversation."
            )
        else:
            rprint(
                "[bold]Hint[/bold]: Press enter to submit your message, and use"
                f" '{END_PROMPT}' to end the conversation."
            )
            rprint(
                "[bold]Hint[/bold]: If you want to submit multiple lines, use the"
                " '--multi-line' option."
            )
        # loop the conversation
        while True:
            # loop the input and check whether the input is valid
            while True:
                rprint("[yellow bold]Enter your message[/yellow bold]:")
                if self.multi_line:
                    input_list = []
                    input = None
                    # loop to get multiple lines input
                    while input != "":
                        input = self.console.input()
                        input_list.append(input)
                    message = "\n".join(input_list).strip()
                else:
                    message = self.console.input().strip()
                # break the loop if input is valid
                if len(message) != 0:
                    break
                # if message is empty, print error message and continue to input
                print_error_msg("Message cannot be empty!\n")

            messages.append(message)
            # print an empty line to separate the input and output
            # only needed in non multi-line mode
            if not self.multi_line:
                rprint()
            rprint("[blue][bold]Model response:[/bold][/blue]")

            if message == END_PROMPT:
                rprint("Bye!")
                raise typer.Exit()

            with Live(Markdown("Thinking..."), auto_refresh=False) as live:
                response = self.client.do(messages=messages, stream=True)
                s = ""
                for resp in response:
                    if not resp["is_end"]:
                        s += resp["result"]
                        live.update(Markdown(s), refresh=True)
            messages.append(s, role=QfRole.Assistant)
            rprint()


def chat_entry(
    model: str = typer.Option(
        DefaultLLMModel.ChatCompletion,
        help="Model name of the chat model.",
        autocompletion=qianfan.ChatCompletion.models,
    ),
    endpoint: Optional[str] = typer.Option(
        None,
        help="Endpoint of the chat model. This option will override `model` option.",
    ),
    # tui: bool = typer.Option(False, help="Using Terminal UI"),
    multi_line: bool = typer.Option(
        False, help="Multi-line mode which need to press enter twice to submit message."
    ),
    list_model: Optional[bool] = list_model_option,
) -> None:
    """
    Chat with the LLM in the terminal.
    """
    client = ChatClient(model, endpoint, multi_line)
    client.chat_in_terminal()

    # if not tui:
    #     client.chat_in_terminal()
    # else:
    #     client.chat_in_tui()
