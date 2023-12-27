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


import typer
from qianfan.dataset import Dataset
from typing import Optional

dataset_app = typer.Typer()

QIANFAN_PATH_PREFIX = "qianfan://"


def extract_id_from_path(path: str):
    if path.startswith(QIANFAN_PATH_PREFIX):
        return int(path[len(QIANFAN_PATH_PREFIX) :])
    return None


def load_dataset(path: str):
    qianfan_dataset_id = extract_id_from_path(path)
    if qianfan_dataset_id:
        return Dataset.load(qianfan_dataset_id=qianfan_dataset_id)
    return Dataset.load(data_file=path)


@dataset_app.command()
def save(
    src: str = typer.Option(..., help="The source of the dataset."),
    dst: str = typer.Option(..., help="The destination of the dataset."),
):
    src_dataset = load_dataset(src)
    dst_dataset_id = extract_id_from_path(dst)
    if dst_dataset_id:
        src_dataset.save(qianfan_dataset_id=dst_dataset_id)
    else:
        src_dataset.save(data_file=dst)


@dataset_app.command()
def view(
    dataset: str = typer.Argument(..., help="The dataset to view."),
    row: Optional[str] = typer.Option(None, help="The row to view."),
    column: Optional[str] = typer.Option(None, help="The column to view."),
):
    dataset = load_dataset(dataset)
    if row is not None:
        print(dataset.list(int(row)))
    else:
        print(dataset[:])


@dataset_app.command()
def predict(
    dataset: str = typer.Argument(..., help="The dataset to predict."),
    model: str = typer.Option(..., help="The model to predict."),
    endpoint: Optional[str] = typer.Option(None, help="The endpoint to predict."),
    is_chat: bool = typer.Option(False, help="Whether the dataset is a chat."),
    output: Optional[str] = typer.Option(None, help="The output file."),
):
    ds = load_dataset(dataset)
    res = ds.test_using_llm(service_model=model)
    res.save(data_file=output)
