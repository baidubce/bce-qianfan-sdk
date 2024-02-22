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


import os
from typing import Any, Dict, List, Optional, Tuple

import typer
from prompt_toolkit import prompt
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.document import Document
from prompt_toolkit.validation import ValidationError
from rich import print as rprint
from rich.console import Group, RenderableType
from rich.live import Live
from rich.markdown import Markdown
from rich.spinner import Spinner
from rich.text import Text

import qianfan
from qianfan import QfRole
from qianfan.common.client.utils import (
    BosPathValidator,
    InputEmptyValidator,
    credential_required,
    print_error_msg,
    render_response_debug_info,
    replace_logger_handler,
)
from qianfan.resources.typing import QfMessages
from qianfan.utils.bos_uploader import BosHelper, parse_bos_path


class PluginInputValidator(InputEmptyValidator):
    """
    Validator for input in plugin
    """

    def validate(self, document: Document) -> None:
        """
        validate input:
        - input must not be empty
        - if input is /image, file path must be provided
        """
        super().validate(document)
        text = document.text.strip()
        if text.startswith(PluginClient.IMAGE_PROMPT):
            path = text[len(PluginClient.IMAGE_PROMPT) :].strip()
            if len(path) == 0:
                raise ValidationError(
                    message="Image file path must be provided (e.g. /image car.jpg)."
                )


class PluginClient(object):
    """
    Client object for the chat command
    """

    END_PROMPT = "/exit"
    RESET_PROMPT = "/reset"
    IMAGE_PROMPT = "/image"
    HELP_PROMPT = "/help"

    HELP_MESSAGES = {
        END_PROMPT: "End the conversation",
        RESET_PROMPT: "Reset the conversation",
        IMAGE_PROMPT: "Attach a local image to the conversation (e.g. /image car.jpg)",
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
        plugins: List[str],
        bos_path: Optional[str],
        **kwargs: Any,
    ) -> None:
        """
        Init the chat client
        """
        if model is not None:
            print_error_msg("ERNIE Bot pulgin is currently not available in sdk.")
            raise typer.Exit(1)
        if endpoint is None:
            print_error_msg("Endpoint must be provided for qianfan plugin.")
            raise typer.Exit(1)
        self.client = qianfan.Plugin(endpoint=endpoint)
        self.msg_history = QfMessages()
        self.multi_line = multi_line
        self.console = replace_logger_handler()
        self.inference_args = kwargs
        self.bos_path = bos_path
        self.plugins = plugins
        self.debug = debug

    def print_hint_msg(self) -> None:
        """
        Print hint message when startup
        """
        if self.multi_line:
            rprint(
                "[bold]Hint[/bold]: [green bold]Press Esc before Enter[/] to submit"
                f" your message, or use '{self.HELP_PROMPT}' to acquire more commands."
            )
        else:
            rprint(
                "[bold]Hint[/bold]: Press enter to submit your message, or use"
                f" '{self.HELP_PROMPT}' to acquire more commands.."
            )
            rprint(
                "[bold]Hint[/bold]: If you want to submit multiple lines, use the"
                " '--multi-line' option."
            )
        rprint(f"[dim]Using qianfan plugin with {self.plugins}...[/]")

    def get_bos_path(self) -> str:
        """
        Get bos path. If bos_path is not provided, prompt user to input
        """
        if self.bos_path is None:
            rprint("Please input bos bucket path [dim](bos:/<bucket>/<path>)[/]: ")
            self.bos_path = prompt("bos:/", validator=BosPathValidator())
            self.bos_path = "bos:/" + self.bos_path
        if not self.bos_path.endswith("/"):
            self.bos_path = self.bos_path + "/"
        return self.bos_path

    def upload_file_to_bos(self, filepath: str) -> Tuple[str, str]:
        """
        Upload file to bos and get bos_url and http_url
        """
        bos_helper = BosHelper()
        bucket, bos_path = parse_bos_path(self.get_bos_path())

        bos_path = bos_path + os.path.basename(filepath)
        with self.console.status("Uploading file to bos..."):
            bos_helper.upload_file_to_bos(filepath, bos_path, bucket)
        url = bos_helper.get_bos_file_shared_url(bos_path, bucket)
        bos_url = f"bos:/{bucket}{bos_path}"
        return bos_url, url

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
        extra_field: Dict[str, Any] = {}
        while True:
            rprint("\n[yellow bold]Enter your message[/yellow bold]:")
            while True:
                message = prompt(
                    multiline=self.multi_line,
                    validator=PluginInputValidator(),
                    completer=self.input_completer,
                ).strip()
                if message.startswith(self.IMAGE_PROMPT):
                    path = message[len(self.IMAGE_PROMPT) :].strip()
                    if not path.startswith("http"):
                        bos_path, http_path = self.upload_file_to_bos(path)
                        rprint(f"File has been uploaded to: {bos_path}")
                        rprint(f"File share url: {http_path}\n")
                        path = http_path
                    rprint(
                        "[yellow bold]Please continue to input your prompt[/yellow"
                        " bold]:"
                    )

                    extra_field["fileurl"] = path
                    continue
                break

            rprint("\n[blue][bold]Model response[/bold][/blue]:")

            if message == self.END_PROMPT:
                rprint("Bye!")
                raise typer.Exit()
            elif message == self.RESET_PROMPT:
                self.msg_history = QfMessages()
                extra_field = {}
                rprint("Chat history has been cleared.")
                continue
            elif message == self.HELP_PROMPT:
                self.print_help_message()
                continue
            else:
                self.msg_history.append(message)

            with Live(
                Spinner("dots", text="Thinking...", style="status.spinner"),
                auto_refresh=True,
                refresh_per_second=24,
                console=self.console,
            ) as live:
                response = self.client.do(
                    message,
                    plugins=self.plugins,
                    llm=self.inference_args,
                    stream=True,
                    history=self.msg_history._to_list()[:-1],
                    **extra_field,
                )

                m = ""
                for r in response:
                    render_list: List[RenderableType] = []
                    m += r["result"]
                    render_list.append(Markdown(m))
                    if not r["is_end"]:
                        render_list.append(
                            Spinner(
                                "dots", text="Generating...", style="status.spinner"
                            )
                        )
                    stat = r.statistic
                    render_list.append(
                        Text.from_markup(
                            "\n[dim]First token latentcy:"
                            f" {stat['first_token_latency']:.2f}s, Total latency:"
                            f" {stat['total_latency']:.2f}s.[/]"
                        )
                    )
                    if r["is_end"]:
                        if "usage" in r:
                            token_usage = r["usage"]
                            render_list.append(
                                Text.from_markup(
                                    f"[dim]Input token: {token_usage['prompt_tokens']},"
                                    " Output token:"
                                    f" {token_usage['completion_tokens']}, Total token:"
                                    f" {token_usage['total_tokens']}.[/]"
                                )
                            )
                        if self.debug:
                            render_list.append(render_response_debug_info(response=r))

                    live.update(Group(*render_list))

            self.msg_history.append(m, role=QfRole.Assistant)


MODEL_ARGUMENTS_PANEL = (
    "Model Arguments (Some arguments are not supported by every model)"
)


@credential_required
def plugin_entry(
    endpoint: Optional[str] = typer.Option(
        ...,
        help="Endpoint of the plugin.",
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
    plugins: str = typer.Option(
        ...,
        help=(
            "Plugins enabled. Use comma(,) to split. (e.g."
            " uuid-zhishiku,uuid-chatocr,uuid-weatherforecast)"
        ),
    ),
    bos_path: Optional[str] = typer.Option(None, help="Bos path used for upload file."),
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
) -> None:
    """
    Chat with the LLM with plugins in the terminal.
    """
    model = None

    extra_args = {}

    def add_if_not_none(key: str, value: Any) -> None:
        if value is not None:
            extra_args[key] = value

    add_if_not_none("temperature", temperature)
    add_if_not_none("top_p", top_p)
    add_if_not_none("penalty_score", penalty_score)
    add_if_not_none("system", system)

    if stop is not None:
        extra_args["stop"] = stop.split(",")

    client = PluginClient(
        model,
        endpoint,
        multi_line,
        debug=debug,
        plugins=plugins.split(","),
        bos_path=bos_path,
        **extra_args,
    )
    client.chat_in_terminal()
