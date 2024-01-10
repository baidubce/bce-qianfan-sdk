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

from concurrent.futures import ThreadPoolExecutor, wait
from typing import Optional, List
from click import Group

import typer
from rich import print as rprint
from rich.console import Console
from rich.live import Live
from rich.markdown import Markdown
from rich.spinner import Spinner

import qianfan
from qianfan import Messages, QfRole
from qianfan.common.client.utils import (
    create_client,
    list_model_option,
    print_error_msg,
)
from qianfan.consts import DefaultLLMModel
from rich.table import Table

from qianfan.errors import InternalError
from qianfan.resources.typing import QfMessages

END_PROMPT = "\exit"


class ChatClient(object):
    """
    Client object for the chat command
    """

    def __init__(self, model: str, endpoint: Optional[str], multi_line: bool) -> None:
        """
        Init the chat client
        """
        self.clients: List[qianfan.ChatCompletion] = []
        models = model.split(",")
        endpoints = endpoint.split(",") if endpoint else []
        for m in models:
            self.clients.append(qianfan.ChatCompletion(model=m))
        for e in endpoints:
            self.clients.append(qianfan.ChatCompletion(endpoint=e))
        self.msg_history = [QfMessages() for _ in range(len(self.clients))]
        self.multi_line = multi_line
        self.console = Console()
        self.thread_pool = ThreadPoolExecutor(max_workers=len(self.clients))

    def chat_in_terminal(self) -> None:
        """
        Chat in terminal
        """

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

            for i in range(len(self.clients)):
                self.msg_history[i].append(message)

            # print an empty line to separate the input and output
            # only needed in non multi-line mode
            if not self.multi_line:
                rprint()
            rprint("[blue][bold]Model response:[/bold][/blue]")

            if message == END_PROMPT:
                rprint("Bye!")
                raise typer.Exit()

            if len(self.clients) == 1:
                with Live(Markdown("Thinking..."), auto_refresh=False) as live:
                    response = self.clients[0].do(
                        messages=self.msg_history[0], stream=True
                    )
                    s = ""
                    for resp in response:
                        if not resp["is_end"]:
                            s += resp["result"]
                            live.update(Markdown(s), refresh=True)
            else:
                msg_list = [["", False] for _ in range(len(self.clients))]

                def gen_table():
                    table = Table()
                    live_list = []
                    for client, msg in zip(self.clients, msg_list):
                        title: str
                        if client._model is not None:
                            title = f"Model [green]{client._model}[/green]"
                        elif client._endpoint is not None:
                            title = f"Endpoint [green]{client._endpoint}[/green]"
                        else:
                            raise InternalError(
                                "No model or endpoint specified in ChatCompletion."
                            )
                        if msg[1] is False:
                            render_title = Spinner("dots", text=title)
                        else:
                            render_title = title
                        table.add_column(render_title, overflow="fold")
                        live_list.append(
                            Markdown(msg[0] if len(msg[0]) != 0 else "Thinking...")
                        )
                    table.add_row(*live_list)
                    return table

                with Live(
                    gen_table(), auto_refresh=True, refresh_per_second=24
                ) as live:

                    def haha(client: qianfan.ChatCompletion, i: int):
                        response = client.do(messages=self.msg_history[i], stream=True)
                        s = ""
                        for resp in response:
                            if not resp["is_end"]:
                                msg_list[i][0] += resp["result"]
                            else:
                                msg_list[i][1] = True
                            live.update(gen_table(), refresh=True)

                    task_list = []
                    for i, client in enumerate(self.clients):
                        task = self.thread_pool.submit(haha, client, i)
                        task_list.append(task)
                    wait(task_list)

                    for i, msg in enumerate(msg_list):
                        self.msg_history[i].append(msg[0], role=QfRole.Assistant)
                    live.update(gen_table(), refresh=True)
            # messages.append(s, role=QfRole.Assistant)
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
