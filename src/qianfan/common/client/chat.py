from typing import Optional

import typer
from rich import print
from rich.console import Console
from rich.live import Live
from rich.markdown import Markdown

import qianfan
from qianfan import Messages, QfRole
from qianfan.components.client.utils import (
    create_client,
    print_error_msg,
)

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
            print(
                "[bold]Hint[/bold]: Press enter [bold]twice[/bold] to submit your"
                f" message, and use '{END_PROMPT}' to end the conversation."
            )
        else:
            print(
                "[bold]Hint[/bold]: Press enter to submit your message, and use"
                f" '{END_PROMPT}' to end the conversation."
            )
            print(
                "[bold]Hint[/bold]: If you want to submit multiple lines, use the"
                " '--multi-line' option."
            )
        # loop the conversation
        while True:
            # loop the input and check whether the input is valid
            while True:
                print("[yellow bold]Enter your message[/yellow bold]:")
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
                print()
            print("[blue][bold]Model response:[/bold][/blue]")

            if message == END_PROMPT:
                print("Bye!")
                raise typer.Exit()

            with Live(Markdown("Thinking..."), auto_refresh=False) as live:
                response = self.client.do(messages=messages, stream=True)
                s = ""
                for resp in response:
                    if not resp["is_end"]:
                        s += resp["result"]
                        live.update(Markdown(s), refresh=True)
            messages.append(s, role=QfRole.Assistant)
            print()

    # def chat_in_tui(self) -> None:
    #     """
    #     Create a terminal UI for the chat.
    #     """
    #     if not check_package_installed("textual"):
    #         print_warn_msg(
    #             "Textual library is required for the enhanced terminal UI experience."
    #             " You can install it using 'pip install textual'."
    #         )
    #         print_warn_msg(
    #             "Without Textual, the program will run in a standard command-line"
    #             " interface mode."
    #         )
    #         print_warn_msg(
    #             "Alternatively, you can use the `--no-tui` option to suppress this"
    #             " warning."
    #         )
    #         return self.chat_in_terminal()
    #     self.chat_in_terminal()


def chat_entry(
    model: str = typer.Option("ERNIE-Bot-turbo", help="Model name"),
    endpoint: Optional[str] = typer.Option(None, help="Endpoint"),
    # tui: bool = typer.Option(False, help="Using Terminal UI"),
    multi_line: bool = typer.Option(False, help="Multi-line mode"),
) -> None:
    """
    Entry of the chat command.
    """
    client = ChatClient(model, endpoint, multi_line)
    client.chat_in_terminal()

    # if not tui:
    #     client.chat_in_terminal()
    # else:
    #     client.chat_in_tui()
