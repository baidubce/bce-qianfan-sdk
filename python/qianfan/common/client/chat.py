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
from concurrent.futures import ThreadPoolExecutor, wait
from typing import Any, List, Optional, Tuple

import typer
from prompt_toolkit import prompt
from prompt_toolkit.completion import WordCompleter
from rich import print as rprint
from rich.console import Group, RenderableType
from rich.live import Live
from rich.markdown import Markdown
from rich.spinner import Spinner
from rich.table import Table
from rich.text import Text

import qianfan
from qianfan import QfRole
from qianfan.common.client.utils import (
    InputEmptyValidator,
    credential_required,
    list_model_option,
    render_response_debug_info,
    replace_logger_handler,
)
from qianfan.consts import DefaultLLMModel
from qianfan.errors import InternalError
from qianfan.resources.llm.chat_completion import ChatCompletion
from qianfan.resources.typing import QfMessages, QfResponse


class ChatClient(object):
    """
    Client object for the chat command
    """

    END_PROMPT = "/exit"
    RESET_PROMPT = "/reset"
    HELP_PROMPT = "/help"

    HELP_MESSAGES = {
        END_PROMPT: "End the conversation",
        RESET_PROMPT: "Reset the conversation",
        HELP_PROMPT: "Print help message",
    }
    input_completer = WordCompleter(
        list(HELP_MESSAGES.keys()), sentence=True, meta_dict=HELP_MESSAGES
    )

    def __init__(
        self,
        model: Optional[str],
        endpoint: Optional[str],
        multi_line: bool,
        debug: bool,
        **kwargs: Any,
    ) -> None:
        """
        Init the chat client
        """
        self.clients: List[qianfan.ChatCompletion] = []
        models = model.split(",") if model else []
        endpoints = endpoint.split(",") if endpoint else []
        for m in models:
            self.clients.append(qianfan.ChatCompletion(model=m))
        for e in endpoints:
            self.clients.append(qianfan.ChatCompletion(endpoint=e))
        self.msg_history: List[Optional[QfMessages]] = [
            QfMessages() for _ in range(len(self.clients))
        ]
        self.multi_line = multi_line
        self.console = replace_logger_handler()
        self.thread_pool = ThreadPoolExecutor(max_workers=len(self.clients))
        self.inference_args = kwargs
        self.debug = debug

    def single_model_response(
        self, msg: Tuple[str, bool, Optional[QfResponse]]
    ) -> RenderableType:
        """
        Renders response of one model
        """
        m, done, resp = msg
        # have not received first token, return a spinner
        if m == "" and not done:
            return Spinner("dots", text="Thinking...", style="status.spinner")
        # render the recieved message
        render_list: List[RenderableType] = [Markdown(m)]
        # if not finished, append a spinner
        if not done:
            render_list.append(
                Spinner("dots", text="Generating...", style="status.spinner")
            )
        if resp is not None:
            # add latency info
            stat = resp.statistic
            render_list.append(
                Text.from_markup(
                    "\n[dim]First token latentcy:"
                    f" {stat['first_token_latency']:.2f}s, Total latency:"
                    f" {stat['total_latency']:.2f}s.[/]"
                )
            )
            # add token usage when finished
            if done:
                token_usage = resp["usage"]
                render_list.append(
                    Text.from_markup(
                        f"[dim]Input token: {token_usage['prompt_tokens']}, Output"
                        f" token: {token_usage['completion_tokens']}, Total token:"
                        f" {token_usage['total_tokens']}.[/]"
                    )
                )
                if self.debug:
                    render_list.append(render_response_debug_info(resp))

        return Group(
            *render_list,
        )

    def _client_name(self, client: ChatCompletion, markup: Optional[str] = None) -> str:
        """
        Generate client name
        """

        def _markup(s: str) -> str:
            if markup is not None:
                return f"[{markup}]{s}[/{markup}]"
            else:
                return s

        name: str
        if client._model is not None:
            name = f"Model {_markup(client._model)}"
        elif client._endpoint is not None:
            name = f"Endpoint {_markup(client._endpoint)}"
        else:
            raise InternalError("No model or endpoint specified in ChatCompletion.")
        return name

    def render_model_response(
        self, msg_list: List[Tuple[str, bool, Optional[QfResponse]]]
    ) -> RenderableType:
        """
        Render responses from multiple models
        """
        if len(msg_list) == 1:
            return self.single_model_response(msg_list[0])
        table = Table(expand=True)
        render_list = []
        for client, msg in zip(self.clients, msg_list):
            title = self._client_name(client, "green")
            table.add_column(title, overflow="fold", ratio=1)
            render_list.append(self.single_model_response(msg))
        table.add_row(*render_list)
        return table

    def print_hint_msg(self) -> None:
        """
        Print hint message when startup
        """
        if self.multi_line:
            rprint(
                "[bold]Hint[/bold]: [green bold]Press Esc before Enter[/] to submit"
                f" your message, and use '{self.END_PROMPT}' to end the conversation."
            )
        else:
            rprint(
                "[bold]Hint[/bold]: Press enter to submit your message, and use"
                f" '{self.END_PROMPT}' to end the conversation."
            )
            rprint(
                "[bold]Hint[/bold]: If you want to submit multiple lines, use the"
                " '--multi-line' option."
            )

    def print_help_message(self) -> None:
        """
        Print command introduction
        """
        for k, v in self.HELP_MESSAGES.items():
            rprint(f"[bold green]{k}[/]: {v}")

    def chat_in_terminal(self) -> None:
        """
        Chat in terminal
        """

        self.print_hint_msg()
        # loop the conversation
        while True:
            rprint("\n[yellow bold]Enter your message[/yellow bold]:")
            message = prompt(
                multiline=self.multi_line,
                validator=InputEmptyValidator(),
                completer=self.input_completer,
            ).strip()

            extra_info = (
                ""
                if len(self.clients) != 1
                else f"({ self._client_name(self.clients[0])})"
            )
            rprint(
                f"\n[blue][bold]Model response[/bold][/blue][dim] {extra_info}[/dim]:"
            )

            if message == self.END_PROMPT:
                rprint("Bye!")
                raise typer.Exit()
            elif message == self.RESET_PROMPT:
                self.msg_history = [QfMessages() for _ in range(len(self.clients))]
                rprint("Chat history has been cleared.")
                continue
            elif message == self.HELP_PROMPT:
                self.print_help_message()
                continue

            for i in range(len(self.clients)):
                msg_history = self.msg_history[i]
                if msg_history is not None:
                    msg_history.append(message)

            # List of (received_msg, is_end, response) for each client
            msg_list: List[Tuple[str, bool, Optional[QfResponse]]] = [
                ("", False, None) for _ in range(len(self.clients))
            ]

            with Live(
                self.render_model_response(msg_list),
                auto_refresh=True,
                refresh_per_second=24,
                console=self.console,
            ) as live:

                def model_response_worker(
                    client: qianfan.ChatCompletion, i: int
                ) -> None:
                    """
                    Worker for each client to recevie message
                    """
                    try:
                        messages = self.msg_history[i]
                        if messages is None:
                            msg_list[i] = (
                                (
                                    "An error was encountered before and this session"
                                    " was terminated."
                                ),
                                True,
                                None,
                            )
                            return
                        response = client.do(
                            messages=messages,
                            stream=True,
                            **self.inference_args,
                        )
                        for resp in response:
                            msg_list[i] = (
                                msg_list[i][0] + resp["result"],
                                resp["is_end"],
                                resp,
                            )
                            live.update(self.render_model_response(msg_list))
                    except Exception as e:
                        msg_list[i] = (
                            msg_list[i][0] + "\n\n**Got Exception**: " + repr(e),
                            True,
                            None,
                        )
                        self.msg_history[i] = None
                    finally:
                        live.update(self.render_model_response(msg_list))

                task_list = []
                for i, client in enumerate(self.clients):
                    task = self.thread_pool.submit(model_response_worker, client, i)
                    task_list.append(task)
                wait(task_list)

                # End the client if there is only one client and got exception
                if len(self.clients) == 1 and self.msg_history[0] is None:
                    raise typer.Exit(1)

                # append response to each chat history
                for i, msg in enumerate(msg_list):
                    msg_history = self.msg_history[i]
                    if msg_history is not None:
                        msg_history.append(msg[0], role=QfRole.Assistant)


MODEL_ARGUMENTS_PANEL = (
    "Model Arguments (Some arguments are not supported by every model)"
)


@credential_required
def chat_entry(
    model: Optional[str] = typer.Option(
        None,
        help=(
            f"Model name of the chat model. {DefaultLLMModel.ChatCompletion} will be"
            " used if no model and endpoint are specified. Use comma(,) to split"
            " multiple models."
        ),
        autocompletion=qianfan.ChatCompletion.models,
    ),
    endpoint: Optional[str] = typer.Option(
        None,
        help="Endpoint of the chat model. Use comma(,) to split multiple endpoints.",
    ),
    # tui: bool = typer.Option(False, help="Using Terminal UI"),
    multi_line: bool = typer.Option(
        False,
        "--multi-line",
        help="Multi-line mode which needs to press Esc before enter to submit message.",
    ),
    debug: bool = typer.Option(
        False,
        "--debug",
        help="Enable debug mode. The request infomation will be printed.",
    ),
    list_model: Optional[bool] = list_model_option,
    temperature: Optional[float] = typer.Option(
        None,
        help=(
            "Controls the randomness of the generated text. A higher temperature makes"
            " the model more creative and produces more diverse, but potentially less"
            " coherent."
        ),
        rich_help_panel=MODEL_ARGUMENTS_PANEL,
    ),
    top_p: Optional[float] = typer.Option(
        None,
        help=(
            "Lower top_p value allows the model to focus on a narrowed set of likely"
            " next tokens, making the response more conherent but less random."
        ),
        rich_help_panel=MODEL_ARGUMENTS_PANEL,
    ),
    top_k: Optional[int] = typer.Option(
        None,
        help="Number of tokens to sample from the top_k distribution.",
        rich_help_panel=MODEL_ARGUMENTS_PANEL,
    ),
    penalty_score: Optional[float] = typer.Option(
        None,
        help="Penalty scores can be applied to discourage repetition.",
        rich_help_panel=MODEL_ARGUMENTS_PANEL,
    ),
    system: Optional[str] = typer.Option(
        None,
        help="Persona setting for the model.",
        rich_help_panel=MODEL_ARGUMENTS_PANEL,
    ),
    stop: Optional[str] = typer.Option(
        None,
        help="Stop words. Use comma to split multiple stop words.",
        rich_help_panel=MODEL_ARGUMENTS_PANEL,
    ),
    max_output_tokens: Optional[int] = typer.Option(
        None,
        help="Maximum number of tokens to output.",
        rich_help_panel=MODEL_ARGUMENTS_PANEL,
    ),
    response_format: Optional[str] = typer.Option(
        None,
        help="Response format (e.g. json_object / text).",
        rich_help_panel=MODEL_ARGUMENTS_PANEL,
    ),
    disable_search: Optional[bool] = typer.Option(
        None, help="Disable search", rich_help_panel=MODEL_ARGUMENTS_PANEL
    ),
    enable_citation: Optional[bool] = typer.Option(
        None, help="Enable citation", rich_help_panel=MODEL_ARGUMENTS_PANEL
    ),
    extra_parameters: Optional[str] = typer.Option(
        None,
        help="Extra parameters for the model. This should be a json string.",
        rich_help_panel=MODEL_ARGUMENTS_PANEL,
    ),
) -> None:
    """
    Chat with the LLM in the terminal.
    """
    if model is None and endpoint is None:
        model = DefaultLLMModel.ChatCompletion

    extra_args = {}

    def add_if_not_none(key: str, value: Any) -> None:
        if value is not None:
            extra_args[key] = value

    add_if_not_none("temperature", temperature)
    add_if_not_none("top_p", top_p)
    add_if_not_none("top_k", top_k)
    add_if_not_none("penalty_score", penalty_score)
    add_if_not_none("system", system)
    add_if_not_none("max_output_tokens", max_output_tokens)
    add_if_not_none("response_format", response_format)
    add_if_not_none("disable_search", disable_search)
    add_if_not_none("enable_citation", enable_citation)

    if stop is not None:
        extra_args["stop"] = stop.split(",")
    if extra_parameters is not None:
        extra_args["extra_parameters"] = json.loads(extra_parameters)

    client = ChatClient(model, endpoint, multi_line, debug=debug, **extra_args)
    client.chat_in_terminal()

    # if not tui:
    #     client.chat_in_terminal()
    # else:
    #     client.chat_in_tui()
