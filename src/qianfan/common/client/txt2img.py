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

import io
from pathlib import Path
from typing import Any, Dict, Optional

import typer
from rich.console import Console

import qianfan
from qianfan import QfResponse
from qianfan.common.client.utils import create_client, print_error_msg, timestamp
from qianfan.consts import DefaultLLMModel
from qianfan.utils.utils import check_package_installed


def txt2img_entry(
    prompt: str = typer.Argument(..., help="The prompt to generate image"),
    negative_prompt: str = typer.Option(
        default="", help="The negative prompt to generate image"
    ),
    model: str = typer.Option(
        DefaultLLMModel.Text2Image,
        help="Model name of the Text2Image model.",
        autocompletion=qianfan.Text2Image.models,
    ),
    endpoint: Optional[str] = typer.Option(
        None,
        help=(
            "Endpoint of the Text2Image model. This option will override `model`"
            " option."
        ),
    ),
    output: Optional[Path] = typer.Option(
        Path(f"./{timestamp()}.jpg"), help="The output file location"
    ),
    plain: bool = typer.Option(False, help="Plain text mode won't use rich text"),
) -> None:
    """
    Generate images based on the provided prompt.
    """
    if check_package_installed("PIL"):
        from PIL import Image
    else:
        print_error_msg(
            "Pillow is required for this command. You can install it using `pip install"
            " Pillow`"
        )
        raise typer.Exit(1)
    client = create_client(qianfan.Text2Image, model, endpoint)
    kwargs: Dict[str, Any] = {}
    if negative_prompt != "":
        kwargs["negative_prompt"] = negative_prompt
    if plain:
        resp = client.do(prompt=prompt, with_decode="base64", **kwargs)
    else:
        with Console().status("Generating"):
            resp = client.do(prompt=prompt, with_decode="base64", **kwargs)
    assert isinstance(resp, QfResponse)
    img_data = resp["body"]["data"][0]["image"]
    img = Image.open(io.BytesIO(img_data))
    # avoid compressing the image
    img.save(output, quality=100, subsampling=0)
    print(f"Image saved to {output}")
