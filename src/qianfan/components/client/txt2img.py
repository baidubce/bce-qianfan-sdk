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
from typing import Optional

import typer
from PIL import Image

import qianfan
from qianfan.components.client.utils import create_client, timestamp
from qianfan.consts import DefaultLLMModel


def txt2img_entry(
    prompt: str = typer.Argument(..., help="The prompt to generate image"),
    negative_prompt: str = typer.Option(
        default="", help="The negative prompt to generate image"
    ),
    model: str = typer.Option(DefaultLLMModel.Text2Image, help="The model to use"),
    endpoint: Optional[str] = typer.Option(None, help="The endpoint to use"),
    output: Optional[Path] = typer.Option(
        Path(f"./{timestamp()}.jpg"), help="The output file location"
    ),
) -> None:
    """
    Generate images from text.
    """
    client = create_client(qianfan.Text2Image, model, endpoint)
    kwargs = {}
    if negative_prompt != "":
        kwargs["negative_prompt"] = negative_prompt
    resp = client.do(prompt=prompt, with_decode="base64", **kwargs)
    img_data = resp["body"]["data"][0]["image"]
    img = Image.open(io.BytesIO(img_data))
    img.save(output, quality=100, subsampling=0)
