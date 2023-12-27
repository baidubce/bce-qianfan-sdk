from typing import Optional

import typer

import qianfan
from qianfan.components.client.chat import chat_entry
from qianfan.components.client.completion import completion_entry
from qianfan.components.client.txt2img import txt2img_entry
from qianfan.components.client.dataset import dataset_app

app = typer.Typer()
app.command(name="chat")(chat_entry)
app.command(name="completion")(completion_entry)
app.command(name="txt2img")(txt2img_entry)
app.add_typer(dataset_app, name="dataset")


def main():
    app()


@app.callback()
def entry(access_key: Optional[str] = "", secret_key: Optional[str] = ""):
    if access_key:
        qianfan.get_config().ACCESS_KEY = access_key
    if secret_key:
        qianfan.get_config().SECRET_KEY = secret_key


if __name__ == "__main__":
    main()
