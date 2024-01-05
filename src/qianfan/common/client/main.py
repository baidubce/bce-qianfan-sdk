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

import qianfan
from qianfan.common.client.chat import chat_entry
from qianfan.common.client.completion import completion_entry
from qianfan.common.client.dataset import dataset_app
from qianfan.common.client.embedding import embedding_entry
from qianfan.common.client.txt2img import txt2img_entry

app = typer.Typer(
    no_args_is_help=True,
    rich_markup_mode="rich",
    context_settings={"help_option_names": ["-h", "--help"]},
)
app.command(name="chat")(chat_entry)
app.command(name="completion")(completion_entry)
app.command(name="txt2img")(txt2img_entry)
app.command(name="embedding", no_args_is_help=True)(embedding_entry)
app.add_typer(dataset_app, name="dataset")


def version_callback(value: bool) -> None:
    """
    Print qianfan sdk version
    """
    if value:
        print(qianfan.__version__)
        raise typer.Exit()


def qianfan_config_callback(
    ctx: typer.Context, param: typer.CallbackParam, value: str
) -> None:
    """
    update qianfan config
    """
    if value is not None and len(value.strip()) > 0:
        config_name = param.name
        if config_name is not None:
            # arguments name should be lowercase of the variable in config
            qianfan_config_name = config_name.upper()
            qianfan.get_config().__setattr__(qianfan_config_name, value)


def main() -> None:
    """
    Main function of qianfan client.
    """
    app()


@app.callback()
def entry(
    access_key: Optional[str] = typer.Option(
        None,
        callback=qianfan_config_callback,
        help=(
            "Access key from"
            " [link=https://console.bce.baidu.com/iam/#/iam/accesslist]Qianfan"
            " IAM[/link]."
            " [link=https://cloud.baidu.com/doc/Reference/s/9jwvz2egb]Reference"
            " here[/link]."
        ),
    ),
    secret_key: Optional[str] = typer.Option(
        None,
        callback=qianfan_config_callback,
        help=(
            "Secret key from"
            " [link=https://console.bce.baidu.com/iam/#/iam/accesslist]Qianfan"
            " IAM[/link]."
            " [link=https://cloud.baidu.com/doc/Reference/s/9jwvz2egb]Reference"
            " here[/link]."
        ),
    ),
    ak: Optional[str] = typer.Option(
        None,
        callback=qianfan_config_callback,
        help=(
            "API key of"
            " [link=https://console.bce.baidu.com/qianfan/ais/console/applicationConsole/application]Qianfan"
            " App[/link]."
            " [link=https://cloud.baidu.com/doc/WENXINWORKSHOP/s/Slkkydake]Reference"
            " here[/link]."
        ),
    ),
    sk: Optional[str] = typer.Option(
        None,
        callback=qianfan_config_callback,
        help=(
            "Secret key"
            " [link=https://console.bce.baidu.com/qianfan/ais/console/applicationConsole/application]Qianfan"
            " App[/link]."
            " [link=https://cloud.baidu.com/doc/WENXINWORKSHOP/s/Slkkydake]Reference"
            " here[/link]."
        ),
    ),
    version: Optional[bool] = typer.Option(
        None,
        "--version",
        "-v",
        callback=version_callback,
        is_eager=True,
        help="Print version.",
    ),
) -> None:
    """
    Qianfan CLI which provides access to various Qianfan services.
    """
    pass


if __name__ == "__main__":
    main()
