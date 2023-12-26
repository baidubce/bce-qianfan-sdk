import typer
import qianfan
from typing import Optional
from qianfan.components.client.chat import chat_app, chat1

app = typer.Typer()
app.add_typer(chat_app, name="chat", invoke_without_command=True)


def main():
    app()


@app.callback()
def main1(ak: Optional[str] = "", sk: Optional[str] = ""):
    if ak:
        qianfan.get_config().ak = ak
    # ...


if __name__ == "__main__":
    main()
