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


import re
from pathlib import Path
from typing import Any, Optional

import typer
from rich.console import Console, Group
from rich.pretty import Pretty
from rich.rule import Rule
from rich.table import Table

import qianfan.common.client.utils as client_utils
from qianfan.common.client.utils import (
    enum_typer,
    print_error_msg,
    print_info_msg,
    print_success_msg,
    timestamp,
)
from qianfan.consts import DefaultLLMModel
from qianfan.dataset import Dataset, DataStorageType, DataTemplateType
from qianfan.dataset.data_source import QianfanDataSource
from qianfan.utils.bos_uploader import parse_bos_path

dataset_app = typer.Typer(no_args_is_help=True)

QIANFAN_PATH_PREFIX = "qianfan://"


def extract_id_from_path(path: str):
    if path.startswith(QIANFAN_PATH_PREFIX):
        id = path[len(QIANFAN_PATH_PREFIX) :]
        try:
            return int(id)
        except ValueError:
            print_error_msg(
                (
                    "Invalid platform dataset url. Shoule be like"
                    f" {QIANFAN_PATH_PREFIX}{{dataset_version_id}}"
                ),
                exit=True,
            )

    return None


def load_dataset(path: str, **kwargs: Any):
    qianfan_dataset_id = extract_id_from_path(path)
    if qianfan_dataset_id:
        return Dataset.load(qianfan_dataset_id=qianfan_dataset_id, **kwargs)
    return Dataset.load(data_file=path, **kwargs)


SAVE_DATASET_PANEL = "Platform Dataset Options (Required when saving to platform)"


@dataset_app.command()
def save(
    src: str = typer.Argument(..., help="The source of the dataset."),
    dst: Optional[str] = typer.Argument(None, help="The destination of the dataset."),
    dataset_name: Optional[str] = typer.Option(
        None, help="The name of the dataset.", rich_help_panel=SAVE_DATASET_PANEL
    ),
    dataset_template_type: Optional[str] = typer.Option(
        "non_sorted_conversation",
        help="The type of the dataset.",
        **enum_typer(DataTemplateType),
        rich_help_panel=SAVE_DATASET_PANEL,
    ),
    dataset_storage_type: Optional[str] = typer.Option(
        "private_bos",
        help="The storage type of the dataset.",
        **enum_typer(DataStorageType),
        rich_help_panel=SAVE_DATASET_PANEL,
    ),
    bos_path: str = typer.Option(
        "",
        help="The storage type.",
        rich_help_panel=SAVE_DATASET_PANEL,
    ),
):
    """Save dataset to platform or local file."""
    console = Console()
    with console.status("Loading dataset..."):
        src_dataset = load_dataset(src)

    if dst is None:
        # create a new dataset
        print_info_msg(
            "No destination specified. A new dataset will be created on the platform."
        )
        client_utils.assert_not_none(bos_path, "bos_path")
        client_utils.assert_not_none(dataset_name, "dataset_name")
        dataset_template_type = DataTemplateType[dataset_template_type]
        dataset_storage_type = DataStorageType[dataset_storage_type]
        bucket, path = parse_bos_path(bos_path)
        with console.status("Saving dataset to platform..."):
            src_dataset.save(
                qianfan_dataset_create_args={
                    "name": dataset_name,
                    "template_type": dataset_template_type,
                    "storage_type": dataset_storage_type,
                    "storage_id": bucket,
                    "storage_path": path,
                },
                replace_source=True,
            )
        data_src = src_dataset.inner_data_source_cache
        assert isinstance(data_src, QianfanDataSource)
        print_success_msg(
            "The data has been saved to a new dataset on the platform. The new dataset"
            " id is: "
            + str(data_src.id)
        )
        return
    dst_dataset_id = extract_id_from_path(dst)
    if dst_dataset_id:
        # save to an existing dataset
        print_info_msg(
            "The data will be appended to an existed dataset which id is"
            f" {dst_dataset_id}."
        )
        bucket, path = parse_bos_path(bos_path)
        region = client_utils.bos_bucket_region(bucket)
        with console.status("Saving dataset to platform..."):
            src_dataset.save(
                qianfan_dataset_id=dst_dataset_id,
                sup_storage_id=bucket,
                sup_storage_path=path,
                sup_storage_region=region,
            )
        print_success_msg(
            "The data has been appended to the dataset on platform. The dataset id is:"
            f" {dst_dataset_id}"
        )
        return
    else:
        # save to local file
        path = Path(dst)
        absolute_path = str(path.absolute())
        print_info_msg("The dataset will be saved to local file.")
        src_dataset.save(data_file=absolute_path)
        print_success_msg("Dataset has beed saved to: " + absolute_path)


@dataset_app.command()
def view(
    dataset: str = typer.Argument(..., help="The dataset to view."),
    row: Optional[str] = typer.Option(None, help="The row to view."),
    column: Optional[str] = typer.Option(None, help="The column to view."),
):
    """
    List dataset.
    """
    # list of (start_idx, end_idx)
    row_list = []
    if row is None:
        row_list.append((0, len(dataset)))
    else:
        row_l = row.split(",")
        num_re = re.compile(r"^(\d+)$")  # example: 12
        num_span_re = re.compile(r"^(\d+)-(\d+)$")  # example: 12-34
        for r in row_l:
            num_match = num_re.fullmatch(r)
            if num_match:
                row_num = int(num_match.group(1))
                row_list.append((row_num, row_num + 1))
                continue
            num_span_match = num_span_re.fullmatch(r)
            if num_span_match:
                start = int(num_span_match.group(1))
                end = int(num_span_match.group(2)) + 1
                row_list.append((start, end))
                continue
            print_error_msg("Invalid row index: " + r)
            raise typer.Exit(1)

    console = Console()
    with console.status("Loading dataset..."):
        dataset: Dataset = load_dataset(dataset)
    table = Table(expand=True)
    if len(dataset) == 0:
        print_error_msg("The dataset is empty.")
        raise typer.Exit(1)

    sample_row = dataset[0]
    if isinstance(sample_row, list):
        sample_data = sample_row[0]
    else:
        sample_data = sample_row

    col_list = column.split(",") if column else list(sample_data.keys())

    # first column will always be the row index
    table.add_column("row", justify="left")
    for key in col_list:
        if key not in sample_data:
            print_error_msg(f"Column '{key}' does not exist in the dataset.")
            raise typer.Exit(1)
        table.add_column(key, justify="left")

    for start, end in row_list:
        for i in range(start, end):
            data = dataset[i]
            if isinstance(data, list):
                for j, item in enumerate(data):
                    table_data = []
                    # only the first row print the row index
                    if j == 0:
                        table_data.append(str(i))
                    else:
                        table_data.append("")
                    for key in col_list:
                        text_content = Pretty(item[key], overflow="fold")
                        if j == 0:
                            # frist row doesn't need rule
                            render_content = text_content
                        else:
                            render_content = Group(Rule(style="white"), text_content)
                        table_data.append(render_content)
                    table.add_row(*table_data, end_section=(j == len(data) - 1))
            else:
                table_data = [str(i)]
                for key in col_list:
                    text_content = Pretty(data[key], overflow="fold")
                    table_data.append(text_content)
                table.add_row(*table_data, end_section=True)

    console.print(table)


@dataset_app.command()
def predict(
    dataset: str = typer.Argument(..., help="The dataset to predict."),
    model: str = typer.Option(
        DefaultLLMModel.ChatCompletion, help="The model to predict."
    ),
    endpoint: Optional[str] = typer.Option(None, help="The endpoint to predict."),
    output: Optional[Path] = typer.Option(
        Path(f"./{timestamp()}.jsonl"), help="The output file location"
    ),
    input_columns: str = typer.Option("prompt", help="The input column."),
    reference_column: Optional[str] = typer.Option(None, help="The reference column."),
):
    """Predict the dataset using a model and save to local file."""
    input_columns = input_columns.split(",")
    console = Console()
    with console.status("Loading dataset..."):
        ds = load_dataset(
            dataset, input_columns=input_columns, reference_column=reference_column
        )
    with console.status("Predicting..."):
        if endpoint is not None:
            result = ds.test_using_llm(service_endpoint=endpoint)
        else:
            result = ds.test_using_llm(service_model=model)
    result.save(data_file=str(output.absolute()))
    print_success_msg("Prediction result has been saved to: " + str(output.absolute()))
