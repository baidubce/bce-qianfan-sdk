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


from typing import List, Optional, Set

import typer
from rich.console import RenderableType
from rich.pretty import Pretty
from rich.table import Table

from qianfan.common.client.dataset import load_dataset
from qianfan.common.client.utils import (
    credential_required,
    print_error_msg,
    print_info_msg,
    print_warn_msg,
    replace_logger_handler,
)
from qianfan.errors import InternalError
from qianfan.evaluation import EvaluationManager
from qianfan.evaluation.consts import (
    QianfanRefereeEvaluatorDefaultMaxScore,
    QianfanRefereeEvaluatorDefaultMetrics,
    QianfanRefereeEvaluatorDefaultSteps,
)
from qianfan.evaluation.evaluator import (
    ManualEvaluatorDimension,
    QianfanEvaluator,
    QianfanManualEvaluator,
    QianfanRefereeEvaluator,
    QianfanRuleEvaluator,
)
from qianfan.model import Model
from qianfan.resources.console.model import Model as ModelResource

evaluation_app = typer.Typer(
    no_args_is_help=True,
    context_settings={"help_option_names": ["-h", "--help"]},
    help="Evaluation utils.",
)

RULE_EVALUATOR_PANEL = "Rule Evaluator Options"
REFEREE_EVALUATOR_PANEL = "Referee Evaluator Options"
MANUAL_EVALUATOR_PANEL = "Manual Evaluator Options"


@credential_required
@evaluation_app.command()
def list_evaluable_models(
    preset: Optional[bool] = typer.Option(
        None,
        help="Whether only print (non-)preset models. Not set to print all models.",
        show_default=False,
    ),
    train_type: Optional[str] = typer.Option(
        None, help="Filter by train type. Use comma(,) to set multiple values."
    ),
    name: Optional[str] = typer.Option(
        None, help="Filter by model name. Use comma(,) to set multiple values."
    ),
) -> None:
    """
    Print evaluable models.
    """
    train_type_set = None if train_type is None else set(train_type.split(","))
    name_set = None if name is None else set(name.split(","))
    model_list = ModelResource.evaluable_model_list()["result"]
    console = replace_logger_handler()
    table = Table(show_lines=True)
    col_list = ["Model Name", "Platform Preset", "Train Type", "Model Version List"]
    for col in col_list:
        table.add_column(col)
    for model in model_list:
        if preset is not None:
            if model["source"] != "PlatformPreset" and preset:
                continue
            if model["source"] == "PlatformPreset" and not preset:
                continue
        if train_type_set is not None:
            if model["trainType"] not in train_type_set:
                continue
        if name_set is not None:
            found = False
            for n in name_set:
                if n in model["modelName"]:
                    found = True
            if not found:
                continue
        row_items: List[RenderableType] = []
        # Model Name
        row_items.append(f"{model['modelName']}\n[dim]{model['modelIdStr']}[/]")
        # Platform Preset
        model_source = model["source"]
        if model_source == "PlatformPreset":
            row_items.append("Yes")
        else:
            row_items.append(f"No\n[dim]{model_source}[/]")
        # Train Type
        row_items.append(model["trainType"])
        # Model Version List
        version_list = [
            f"{version['version']} [dim]({version['modelVersionIdStr']})[/]"
            for version in model["modelVersionList"]
        ]
        row_items.append("\n".join(version_list))
        table.add_row(*row_items)
    console.print(table)


def list_evaluable_models_callback(
    ctx: typer.Context, param: typer.CallbackParam, value: bool
) -> None:
    if value:
        print_warn_msg(
            "This option is [bold]deprecated[/]. Use `qianfan evaluation"
            " list-evaluable-models` instead."
        )
        list_evaluable_models(None, None, None)
        raise typer.Exit()


@evaluation_app.command()
@credential_required
def run(
    models: List[str] = typer.Argument(
        ..., help="List of model version ids to be evaluated."
    ),
    dataset_id: str = typer.Option(..., help="Dataset id."),
    enable_rule_evaluator: bool = typer.Option(False, help="Enable rule evaluator."),
    using_similarity: bool = typer.Option(
        QianfanRuleEvaluator().using_similarity,
        help="Using similarity to evaluate the results.",
        rich_help_panel=RULE_EVALUATOR_PANEL,
    ),
    using_accuracy: bool = typer.Option(
        QianfanRuleEvaluator().using_accuracy,
        help="Using accuracy to evaluate the results.",
        rich_help_panel=RULE_EVALUATOR_PANEL,
    ),
    stop_words: Optional[str] = typer.Option(
        QianfanRuleEvaluator().stop_words,
        help="Stop words.",
        rich_help_panel=RULE_EVALUATOR_PANEL,
    ),
    enable_referee_evaluator: bool = typer.Option(
        False, help="Enable referee evaluator."
    ),
    app_id: Optional[int] = typer.Option(
        None,
        help=(
            "The appid to which the model belongs to. The model will be used to"
            " evaluate the results."
        ),
        rich_help_panel=REFEREE_EVALUATOR_PANEL,
    ),
    prompt_metrics: str = typer.Option(
        QianfanRefereeEvaluatorDefaultMetrics,
        help="Metrics for the model to evaluate the results.",
        rich_help_panel=REFEREE_EVALUATOR_PANEL,
    ),
    prompt_steps: str = typer.Option(
        QianfanRefereeEvaluatorDefaultSteps,
        help="Steps for the model to evaluate the results.",
        rich_help_panel=REFEREE_EVALUATOR_PANEL,
    ),
    prompt_max_score: int = typer.Option(
        QianfanRefereeEvaluatorDefaultMaxScore,
        help="Max score of the evaluation result.",
        rich_help_panel=REFEREE_EVALUATOR_PANEL,
    ),
    enable_manual_evaluator: bool = typer.Option(
        False, help="Enable manual evaluator."
    ),
    dimensions: Optional[str] = typer.Option(
        None,
        help="Dimensions for evaluation. Use ',' to split multiple dimensions.",
        rich_help_panel=MANUAL_EVALUATOR_PANEL,
    ),
    list_evaluable_models: Optional[bool] = typer.Option(
        None,
        "--list-evaluable-models",
        callback=list_evaluable_models_callback,
        is_eager=True,
        help="Print evaluable models.",
    ),
) -> None:
    """
    Run evaluation task.

    At least one evaluator should be enabled.
    Manual evaluator may not be mixed with other evaluators.
    """
    ds = load_dataset(dataset_id)
    model_list = [Model(version_id=m) for m in models]
    console = replace_logger_handler()
    evaluators: List[QianfanEvaluator] = []
    if enable_rule_evaluator:
        evaluators.append(
            QianfanRuleEvaluator(
                using_accuracy=using_accuracy,
                using_similarity=using_similarity,
                stop_words=stop_words,
            )
        )
    if enable_referee_evaluator:
        if app_id is None:
            print_error_msg("App_id is required for referee evaluator.")
            raise typer.Exit(1)
        evaluators.append(
            QianfanRefereeEvaluator(
                app_id=app_id,
                prompt_metrics=prompt_metrics,
                prompt_steps=prompt_steps,
                prompt_max_score=prompt_max_score,
            )
        )
    if enable_manual_evaluator:
        if dimensions is None:
            print_error_msg("Dimensions are required for manual evaluator.")
            raise typer.Exit(1)
        if len(evaluators) != 0:
            print_warn_msg("Manual evaluator may not be mixed with other evaluators.")
        dimension_list = dimensions.split(",")
        evaluators.append(
            QianfanManualEvaluator(
                evaluation_dimensions=[
                    ManualEvaluatorDimension(dimension=dim) for dim in dimension_list
                ]
            )
        )
    if len(evaluators) == 0:
        print_error_msg("At least one evaluator should be enabled.", exit=True)

    em = EvaluationManager(qianfan_evaluators=evaluators)
    with console.status("Evaluating..."):
        result = em.eval(model_list, ds)
    eval_task_id = em.task_id
    if eval_task_id is None:
        raise InternalError("Evaluation task id should not be None")
    if result is None or result.metrics is None:
        print_info_msg(
            "The data has been processed. Since manual evaluator is enabled, please go"
            " to https://console.bce.baidu.com/qianfan/modelcenter/model/manual/detail/task/{task_id}"
            " to evalate the results."
        )
        raise typer.Exit(0)
    table = Table()
    cols = list(result.metrics.keys())
    table.add_column("")
    for col in cols:
        table.add_column(col)
    keys: Set[str] = set()
    for k, v in result.metrics.items():
        keys = keys.union(set(v.keys()))
    for k in keys:
        vals = []
        for col in cols:
            vals.append(Pretty(result.metrics[col].get(k, None), overflow="fold"))
        table.add_row(k, *vals)
    console.print(table)
