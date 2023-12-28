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
from qianfan.common.client.txt2img import txt2img_entry

app = typer.Typer()
app.command(name="chat")(chat_entry)
app.command(name="completion")(completion_entry)
app.command(name="txt2img")(txt2img_entry)


def main() -> None:
    """
    Main function of qianfan client.
    """
    app()


@app.callback()
def entry(access_key: Optional[str] = "", secret_key: Optional[str] = "") -> None:
    """
    entry of the whole client
    init global qianfan config
    """
    if access_key:
        qianfan.get_config().ACCESS_KEY = access_key
    if secret_key:
        qianfan.get_config().SECRET_KEY = secret_key


if __name__ == "__main__":
    main()
