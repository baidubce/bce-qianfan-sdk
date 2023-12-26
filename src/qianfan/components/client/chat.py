from itertools import cycle
from typing import Type

import typer
from textual.app import App, CSSPathType
from textual.containers import Horizontal, ScrollableContainer
from textual.driver import Driver
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Footer, Header, Input, Markdown

import qianfan
from qianfan import Messages

chat_app = typer.Typer()


class MessageBox(Markdown):
    pass


class ChatFrontend(App):
    TITLE = "Qianfan Chat"
    CSS_PATH = "style.tcss"

    def __init__(
        self,
        driver_class: Type[Driver] | None = None,
        css_path: CSSPathType | None = None,
        watch_css: bool = False,
    ):
        super().__init__(driver_class, css_path, watch_css)
        self.messages = Messages()
        self.client = qianfan.ChatCompletion()

    def compose(self):
        yield Header()
        yield ScrollableContainer(id="conversation_box")
        with Horizontal(id="input_box"):
            yield Input(placeholder="Enter your message", id="message_input")
            # yield Button(label="Send", variant="success", id="send_button")
        yield Footer()

    async def on_input_submitted(self) -> None:
        await self.chat()

    async def chat(self):
        input = self.query_one("#message_input", Input)
        conv_ = self.query_one("#conversation_box", ScrollableContainer)
        input_val = input.value
        box = MessageBox()
        box.update(input.value)
        conv_.mount(box)
        conv_.scroll_end()
        with input.prevent(Input.Changed):
            input.value = ""
        ans_box = MessageBox()
        conv_.mount(ans_box)
        conv_.scroll_end()
        x = ""
        resp = await self.client.ado(
            messages=[
                {
                    "role": "user",
                    "content": input_val,
                }
            ],
            stream=True,
        )
        async for r in resp:
            if not r["is_end"]:
                x += r["result"]
                ans_box.update(x)

                conv_.scroll_end()


@chat_app.callback()
def chat1(test: str = ""):
    app = ChatFrontend()
    app.run()
