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
from typing import Any, List, Optional

import typer
from rich.console import Group
from rich.pretty import Pretty
from rich.rule import Rule
from rich.table import Table

import qianfan.common.client.utils as client_utils
from qianfan.common.client.utils import (
    check_credential,
    credential_required,
    enum_typer,
    print_error_msg,
    print_info_msg,
    print_success_msg,
    replace_logger_handler,
    timestamp,
)
from qianfan.consts import DefaultLLMModel
from qianfan.dataset import (
    Dataset,
    DataStorageType,
    DataTemplateType,
)
from qianfan.dataset.data_source import QianfanDataSource
from qianfan.utils.bos_uploader import parse_bos_path

dataset_app = typer.Typer(
    no_args_is_help=True,
    context_settings={"help_option_names": ["-h", "--help"]},
    help="Dataset utils.",
)

QIANFAN_PATH_PREFIX = "qianfan://"


def extract_id_from_path(path: str) -> Optional[str]:
    """
    Extract dataset id from path.
    Return 0 if path is not a qianfan dataset.
    """
    if path.startswith(QIANFAN_PATH_PREFIX):
        id = path[len(QIANFAN_PATH_PREFIX) :]
        return id
    if path.startswith("ds-"):
        return path

    return None


def load_dataset(path: str, **kwargs: Any) -> Dataset:
    """Load dataset from platform or local file based on the format of path."""
    qianfan_dataset_id = extract_id_from_path(path)
    if qianfan_dataset_id:
        return Dataset.load(qianfan_dataset_id=qianfan_dataset_id, **kwargs)
    return Dataset.load(data_file=path, **kwargs)


PANEL_FOR_CREATE_DATASET = (
    "Platform Dataset Options (Required when creating a new dataset on platform)"
)


@dataset_app.command()
@credential_required
def save(
    src: str = typer.Argument(
        ...,
        help=(
            "The source of the dataset. The value can be a file path or qianfan"
            " dataset url (qianfan://{dataset_version_id})."
        ),
    ),
    dst: Optional[str] = typer.Argument(
        None,
        help=(
            "The destination of the dataset. The dataset will be saved to a file if the"
            " value is a path. Alternatively, the dataset can be appended to an"
            " existing dataset on the platform if an qianfan dataset url is provided"
            " (qianfan://{dataset_version_id}). If this value is not provided, a new"
            " dataset will be created on the platform."
        ),
    ),
    dataset_name: Optional[str] = typer.Option(
        None,
        help="The name of the dataset on the platform.",
        rich_help_panel=PANEL_FOR_CREATE_DATASET,
    ),
    dataset_template_type: str = typer.Option(
        "non_sorted_conversation",
        help="The type of the dataset.",
        **enum_typer(DataTemplateType),
        rich_help_panel=PANEL_FOR_CREATE_DATASET,
    ),
    dataset_storage_type: str = typer.Option(
        "private_bos",
        help="The storage type of the dataset.",
        **enum_typer(DataStorageType),
        rich_help_panel=PANEL_FOR_CREATE_DATASET,
    ),
    bos_path: str = typer.Option(
        "",
        help=(
            "Path to the dataset file stored on BOS. Required when saving to the"
            " platform. (e.g. bos://bucket/path/)"
        ),
    ),
) -> None:
    """Save dataset to platform or local file."""
    console = replace_logger_handler()
    with console.status("Loading dataset..."):
        src_dataset = load_dataset(src)

    if dst is None:
        # create a new dataset
        print_info_msg(
            "No destination specified. A new dataset will be created on the platform."
        )
        assert (
            bos_path is not None
        ), "bos_path is required when saving to a new dataset."
        assert (
            dataset_name is not None
        ), "dataset_name is required when saving to a new dataset."

        bucket, path = parse_bos_path(bos_path)
        with console.status("Saving dataset to platform..."):
            src_dataset = src_dataset.save(
                qianfan_dataset_create_args={
                    "name": dataset_name,
                    "template_type": DataTemplateType[dataset_template_type],
                    "storage_type": DataStorageType[dataset_storage_type],
                    "storage_id": bucket,
                    "storage_path": path,
                },
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
        dst_path = Path(dst)
        dst_abs_path = str(dst_path.absolute())
        print_info_msg("The dataset will be saved to local file.")
        src_dataset.save(data_file=dst_abs_path)
        print_success_msg("Dataset has beed saved to: " + dst_abs_path)


@dataset_app.command()
@credential_required
def download(
    dataset_id: str = typer.Argument(
        ...,
        help=(
            "The version id of the dataset on the qianfan platform. The value can be"
            " qianfan dataset id or url(qianfan://{dataset_version_id})."
        ),
    ),
    output: Path = typer.Option(Path(f"{timestamp()}.jsonl"), help="Output file path."),
) -> None:
    """Download dataset to local file."""
    dataset_path = extract_id_from_path(dataset_id)
    if dataset_path is None:
        print_error_msg("Invalid dataset id.")
        raise typer.Exit(1)
    save(dataset_id, str(output.absolute()))


@dataset_app.command()
@credential_required
def upload(
    path: Path = typer.Argument(
        ...,
        help="The path of the dataset file.",
    ),
    dst: Optional[str] = typer.Argument(
        None,
        help=(
            "The destination of the dataset. If this value is not provided, a new"
            " dataset will be created on the platform. Alternatively, the dataset can"
            " be appended to an existing dataset on the platform if an qianfan dataset"
            " id or url(qianfan://{dataset_version_id}) is provided . "
        ),
    ),
    dataset_name: Optional[str] = typer.Option(
        None,
        help="The name of the dataset on the platform.",
    ),
    bos_path: str = typer.Option(
        ...,
        help=(
            "Path to the dataset file stored on BOS. Required when saving to the"
            " platform. (e.g. bos://bucket/path/)"
        ),
    ),
    dataset_template_type: str = typer.Option(
        "non_sorted_conversation",
        help="The type of the dataset.",
        **enum_typer(DataTemplateType),
    ),
    dataset_storage_type: str = typer.Option(
        "private_bos",
        help="The storage type of the dataset.",
        **enum_typer(DataStorageType),
    ),
) -> None:
    """Upload dataset to platform."""
    if dst is not None:
        dataset_id = extract_id_from_path(dst)
        if dataset_id is None:
            print_error_msg("Invalid dst dataset id.")
            raise typer.Exit(1)
    save(
        str(path.absolute()),
        dst,
        dataset_name=dataset_name,
        dataset_template_type=dataset_template_type,
        dataset_storage_type=dataset_storage_type,
        bos_path=bos_path,
    )


@dataset_app.command()
def view(
    dataset: str = typer.Argument(
        ...,
        help=(
            "The dataset to view. The value can be a file path or qianfan"
            " dataset url (qianfan://{dataset_version_id})."
        ),
    ),
    row: Optional[str] = typer.Option(
        None,
        help=(
            "The row to view. Use commas(,) to view multiple rows and dashes(-) to"
            " denote a range of data (e.g. 1,3-5,12). By default, only the top 5 rows"
            " will be displayed. Alternatively, use '--row all' to view all rows."
        ),
    ),
    column: Optional[str] = typer.Option(
        None,
        help=(
            "The columns to view. Use comma(,) to separate the names of each column."
            " (e.g. prompt,response)"
        ),
    ),
    raw: bool = typer.Option(False, "--raw", help="Print raw data."),
) -> None:
    """
    View the content of the dataset.
    """
    console = replace_logger_handler()
    if extract_id_from_path(dataset) is not None:
        check_credential()
    with console.status("Loading dataset..."):
        ds = load_dataset(dataset)
    # list of (start_idx, end_idx)
    row_list = []
    if row is None:
        print_info_msg(
            "No row index provided, only top 5 rows will be displayed. Or use '--row"
            " all' to display all rows."
        )
        row_list.append((0, min(len(ds), 5)))
    elif row == "all":
        row_list.append((0, len(ds)))
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

    table = Table(expand=True)
    if len(ds) == 0:
        print_error_msg("The dataset is empty.")
        raise typer.Exit(1)

    sample_row = ds[0]
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
            data = ds[i]
            if raw:
                print(data)
                continue
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
                        render_content: Any
                        if j == 0:
                            # frist row doesn't need rule
                            render_content = text_content
                        else:
                            render_content = Group(Rule(style="white"), text_content)
                        table_data.append(render_content)
                    table.add_row(*table_data, end_section=(j == len(data) - 1))
            else:
                table_data_list: List[Any] = [str(i)]
                for key in col_list:
                    text_content = Pretty(data[key], overflow="fold")
                    table_data_list.append(text_content)
                table.add_row(*table_data_list, end_section=True)
    if not raw:
        console.print(table)


@dataset_app.command()
@credential_required
def predict(
    dataset: str = typer.Argument(
        ...,
        help=(
            "The dataset to predict. The value can be a file path or qianfan"
            " dataset url (qianfan://{dataset_version_id})."
        ),
    ),
    model: str = typer.Option(
        DefaultLLMModel.ChatCompletion, help="The model used to predict."
    ),
    endpoint: Optional[str] = typer.Option(
        None,
        help="The endpoint used to predict. The option will override 'model' option.",
    ),
    output: Path = typer.Option(
        Path(f"./{timestamp()}.jsonl"), help="The output dataset file location."
    ),
    input_columns: str = typer.Option("prompt", help="The input name of column."),
    reference_column: Optional[str] = typer.Option(None, help="The reference column."),
) -> None:
    """Predict the dataset using a model and save to local file."""
    input_column_list = input_columns.split(",")
    console = replace_logger_handler()
    with console.status("Loading dataset..."):
        ds = load_dataset(
            dataset, input_columns=input_column_list, reference_column=reference_column
        )
    with console.status("Predicting..."):
        if endpoint is not None:
            result = ds.test_using_llm(service_endpoint=endpoint)
        else:
            result = ds.test_using_llm(service_model=model)
    result.save(data_file=str(output.absolute()))
    print_success_msg("Prediction result has been saved to: " + str(output.absolute()))
