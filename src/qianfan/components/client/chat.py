from typing import Optional

import typer
from rich import print
from rich.live import Live
from rich.markdown import Markdown

import qianfan
from qianfan import Messages, QfRole
from qianfan.components.client.utils import NewLinePrompt, create_client
from qianfan.utils.logging import log_warn
from qianfan.utils.utils import check_package_installed


def chat_in_terminal(client: qianfan.ChatCompletion) -> None:
    messages = Messages()
    while True:
        message = NewLinePrompt.ask(
            "[yellow bold]Enter your message[/yellow bold] (use '\exit' to end)"
        )
        messages.append(message)
        print("\n[blue][bold]Model response:[/bold][/blue]")

        if message == "\exit":
            print("Bye!")
            raise typer.Exit()

        with Live(Markdown("Thinking..."), auto_refresh=False) as live:
            response = client.do(messages=messages, stream=True)
            s = ""
            for resp in response:
                if not resp["is_end"]:
                    s += resp["result"]
                    live.update(Markdown(s), refresh=True)
        messages.append(s, role=QfRole.Assistant)
        print()


def chat_in_tui(client: qianfan.ChatCompletion) -> None:
    if not check_package_installed("textual"):
        log_warn(
            "Textual library is required for the enhanced terminal UI experience. You"
            " can install it using `pip install textual`. Without Textual, the"
            " program will run in a standard command-line interface mode."
            " Alternatively, you can use the `--plain` option to suppress this warning."
        )
        return chat_in_terminal(client)
    chat_in_terminal(client)



def chat_entry(
    model: str = typer.Option("ERNIE-Bot-turbo", help="Model name"),
    endpoint: Optional[str] = typer.Option(None, help="Endpoint"),
    plain: bool = typer.Option(False, help="Plain text mode"),
):
    client = create_client(qianfan.ChatCompletion, model, endpoint)

    if plain:
        chat_in_terminal(client)
    else:
        chat_in_tui(client)
