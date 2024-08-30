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
from typing import Any, Dict, Optional

import click
import rich.markup
import typer
from typer.completion import completion_init, install_callback, show_callback

import qianfan
from qianfan.common.cli.api import api_app
from qianfan.common.cli.chat import chat_entry
from qianfan.common.cli.completion import completion_entry
from qianfan.common.cli.dataset import dataset_app
from qianfan.common.cli.embedding import embedding_entry
from qianfan.common.cli.evaluation import evaluation_app
from qianfan.common.cli.plugin import plugin_entry
from qianfan.common.cli.trainer import trainer_app
from qianfan.common.cli.txt2img import txt2img_entry
from qianfan.common.cli.utils import (
    credential_required,
    print_error_msg,
    print_info_msg,
)
from qianfan.config import encoding
from qianfan.utils.utils import check_dependency

app = typer.Typer(
    no_args_is_help=True,
    rich_markup_mode="rich",
    context_settings={"help_option_names": ["-h", "--help"]},
    add_completion=False,
)
app.command(name="chat")(chat_entry)
app.command(name="completion")(completion_entry)
app.command(name="txt2img")(txt2img_entry)
app.command(name="embedding", no_args_is_help=True)(embedding_entry)
app.command(name="plugin")(plugin_entry)
app.add_typer(dataset_app, name="dataset")
app.add_typer(trainer_app, name="trainer")
app.add_typer(evaluation_app, name="evaluation")
app.add_typer(api_app, name="api")

_enable_traceback = False


@app.command(name="openai")
@credential_required
def openai(
    host: Optional[str] = typer.Option(
        None,
        "--host",
        "-h",
        help="Host to bind. [dim]\[default: 0.0.0.0][/]",
        show_default=False,
    ),
    port: Optional[int] = typer.Option(
        None,
        "--port",
        "-p",
        help="Port of the server. [dim]\[default: 8001][/]",
        show_default=False,
    ),
    detach: Optional[bool] = typer.Option(
        None,
        "--detach",
        "-d",
        help="Run the server in background.",
    ),
    ignore_system: Optional[bool] = typer.Option(
        None,
        help="Ignore system messages in input. [dim]\[default: True][/]",
        show_default=False,
    ),
    log_file: Optional[str] = typer.Option(None, help="Log file path."),
    api_key: Optional[str] = typer.Option(
        None, help="API key used for authentication in proxy server."
    ),
    config_file: Optional[str] = typer.Option(
        None, help="Config file path.", show_default=False
    ),
) -> None:
    """
    Create an openai wrapper server.
    """
    check_dependency("openai", ["fastapi", "uvicorn"])
    from qianfan.common.cli.openai_adapter import entry as openai_entry

    default_config = {
        "host": "0.0.0.0",
        "port": 8001,
        "detach": False,
        "ignore_system": True,
        "log_file": None,
        "model_mapping": None,
        "api_key": None,
    }
    adapter_config = {}
    if config_file is not None:
        import yaml

        with open(config_file, "r", encoding=encoding()) as f:
            config = yaml.safe_load(f)
        adapter_config = config.get("openai_adapter")
        if adapter_config is None:
            raise ValueError("Config file should contain a key named `openai_adapter`.")
    if ignore_system is None and adapter_config.get("ignore_system") is None:
        print_info_msg(
            "`--no-ignore-system` is not set. System messages will be ignored by"
            " default since most system messages for openai is not suitable for ERNIE"
            " model."
        )
        print()

    merged_config = {**default_config, **adapter_config}

    openai_entry(
        host=host if host is not None else merged_config["host"],
        port=port if port is not None else merged_config["port"],
        detach=detach if detach is not None else merged_config["detach"],
        log_file=log_file if log_file is not None else merged_config["log_file"],
        ignore_system=(
            ignore_system
            if ignore_system is not None
            else merged_config["ignore_system"]
        ),
        model_mapping=merged_config["model_mapping"],
        api_key=api_key if api_key is not None else merged_config["api_key"],
    )


@app.command(name="proxy")
@credential_required
def proxy(
    host: str = typer.Option("0.0.0.0", "--host", "-h", help="Host to bind."),
    base_port: int = typer.Option(
        8002, "--base-port", "-b", help="Port of the base server."
    ),
    console_port: int = typer.Option(
        8003, "--console-port", "-c", help="Port of the console server."
    ),
    detach: bool = typer.Option(
        False,
        "--detach",
        "-d",
        help="Run the server in background.",
    ),
    log_file: Optional[str] = typer.Option(None, help="Log file path."),
    mock_port: int = typer.Option(
        -1, "--mock-port", "-m", help="Port of the Mock server."
    ),
    ssl_keyfile: str = typer.Option("", "--ssl-keyfile", help="SSL key file"),
    ssl_certfile: str = typer.Option("", "--ssl-certfile", help="SSL certificate file"),
    ssl_keyfile_password: str = typer.Option(
        "", "--ssl-keyfile-password", help="SSL keyfile password"
    ),
    ssl_version: int = typer.Option(
        17,
        "--ssl-version",
        help="SSL version to use (see stdlib ssl module's) [default: 17]",
    ),
    ssl_cert_reqs: int = typer.Option(
        0,
        "--ssl-cert-reqs",
        help=(
            "Whether client certificate is required (see stdlib ssl module's) "
            " [default: 0]"
        ),
    ),
    ssl_ca_certs: str = typer.Option("", "--ssl-ca-certs", help="CA certificates file"),
    ssl_ciphers: str = typer.Option(
        "TLSv1",
        "--ssl-ciphers",
        help="Ciphers to use (see stdlib ssl module's) [default: TLSv1]",
    ),
    access_token: str = typer.Option("", "--access-token", help="Access token"),
    direct: bool = typer.Option(False, "--direct", help="Direct connection to server"),
) -> None:
    """
    Create a proxy server.
    """
    check_dependency("openai", ["fastapi", "uvicorn"])
    from qianfan.common.cli.proxy import entry as proxy_entry

    ssl_config: Dict[str, Any] = {}
    if ssl_keyfile:
        ssl_config["ssl_keyfile"] = ssl_keyfile
    if ssl_certfile:
        ssl_config["ssl_certfile"] = ssl_certfile
    if ssl_keyfile_password:
        ssl_config["ssl_keyfile_password"] = ssl_keyfile_password
    if ssl_ca_certs:
        ssl_config["ssl_ca_certs"] = ssl_ca_certs

    if ssl_config:
        ssl_config["ssl_version"] = ssl_version
        ssl_config["ssl_cert_reqs"] = ssl_cert_reqs
        ssl_config["ssl_ciphers"] = ssl_ciphers
    proxy_entry(
        host=host,
        base_port=base_port,
        console_port=console_port,
        detach=detach,
        log_file=log_file,
        mock_port=mock_port,
        ssl_config=ssl_config,
        access_token=access_token,
        direct=direct,
    )


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
    try:
        completion_init()
        app()
    except Exception as e:
        if _enable_traceback:
            raise
        else:
            print_error_msg(rich.markup.escape(str(e)))


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
    enable_traceback: bool = typer.Option(
        False, "--enable-traceback", help="Print traceback when exception is thrown."
    ),
    install_completion: bool = typer.Option(
        None,
        "--install-shell-autocomplete",
        is_flag=True,
        callback=install_callback,
        expose_value=False,
        help="Install the auto completion script for the specified shell.",
    ),
    show_completion: bool = typer.Option(
        None,
        "--show-shell-autocomplete",
        is_flag=True,
        callback=show_callback,
        expose_value=False,
        help=(
            "Show the auto completion script for the specified shell, to copy it or"
            " customize the installation."
        ),
    ),
    log_level: str = typer.Option(
        "WARN",
        help="Set log level.",
        click_type=click.Choice(["DEBUG", "INFO", "WARN", "ERROR", "TRACE"]),
    ),
) -> None:
    """
    Qianfan CLI which provides access to various Qianfan services.
    """
    global _enable_traceback
    _enable_traceback = enable_traceback
    qianfan.enable_log(log_level)


if __name__ == "__main__":
    main()
