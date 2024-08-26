# # Copyright (c) 2024 Baidu, Inc. All Rights Reserved.
# #
# # Licensed under the Apache License, Version 2.0 (the "License");
# # you may not use this file except in compliance with the License.
# # You may obtain a copy of the License at
# #
# #     http://www.apache.org/licenses/LICENSE-2.0
# #
# # Unless required by applicable law or agreed to in writing, software
# # distributed under the License is distributed on an "AS IS" BASIS,
# # WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# # See the License for the specific language governing permissions and
# # limitations under the License.


# from typing import List, Optional, Set

# import typer
# from rich.console import RenderableType
# from rich.pretty import Pretty
# from rich.table import Table

# from qianfan.common.client.dataset import load_dataset
# from qianfan.common.client.utils import (
#     credential_required,
#     print_error_msg,
#     print_info_msg,
#     print_warn_msg,
#     replace_logger_handler,
# )
# from qianfan.errors import InternalError
# from qianfan.evaluation import EvaluationManager
# from qianfan.evaluation.consts import (
#     QianfanRefereeEvaluatorDefaultMaxScore,
#     QianfanRefereeEvaluatorDefaultMetrics,
#     QianfanRefereeEvaluatorDefaultSteps,
# )
# from qianfan.evaluation.evaluator import (
#     ManualEvaluatorDimension,
#     QianfanEvaluator,
#     QianfanManualEvaluator,
#     QianfanRefereeEvaluator,
#     QianfanRuleEvaluator,
# )
# from qianfan.model import Model
# from qianfan.resources.console.model import Model as ModelResource

# model_app = typer.Typer(
#     no_args_is_help=True,
#     context_settings={"help_option_names": ["-h", "--help"]},
#     help="model utils.",
# )

# RULE_EVALUATOR_PANEL = "Rule Evaluator Options"
# REFEREE_EVALUATOR_PANEL = "Referee Evaluator Options"
# MANUAL_EVALUATOR_PANEL = "Manual Evaluator Options"


# @credential_required
# @model_app.command()
# def list_evaluable_models(
#     preset: Optional[bool] = typer.Option(
#         None,
#         help="Whether only print preset models. Not set to print all models.",
#         show_default=False,
#     ),
#     custom: Optional[bool] = typer.Option(
#         None,
#         help="Whether only print custom models. Not set to print all models.",
#         show_default=False,
#     ),
#     time_desc: Optional[str] = typer.Option(
#         None,
#         help="Sorted by time descending order.",
#     ),
#     name: Optional[str] = typer.Option(
#         None, help="Filter by model name. Use comma(,) to set multiple values."
#     ),
# ) -> None:
#     """
#     Print models.
#     """
#     train_type_set = None if train_type is None else set(train_type.split(","))
#     name_set = None if name is None else set(name.split(","))
#     model_list = ModelResource.evaluable_model_list()["result"]
#     console = replace_logger_handler()
#     table = Table(show_lines=True)
#     col_list = ["Model Name", "Platform Preset", "Train Type", "Model Version List"]
#     for col in col_list:
#         table.add_column(col)
#     for model in model_list:
#         if preset is not None:
#             if model["source"] != "PlatformPreset" and preset:
#                 continue
#             if model["source"] == "PlatformPreset" and not preset:
#                 continue
#         if train_type_set is not None:
#             if model["trainType"] not in train_type_set:
#                 continue
#         if name_set is not None:
#             found = False
#             for n in name_set:
#                 if n in model["modelName"]:
#                     found = True
#             if not found:
#                 continue
#         row_items: List[RenderableType] = []
#         # Model Name
#         row_items.append(f"{model['modelName']}\n[dim]{model['modelIdStr']}[/]")
#         # Platform Preset
#         model_source = model["source"]
#         if model_source == "PlatformPreset":
#             row_items.append("Yes")
#         else:
#             row_items.append(f"No\n[dim]{model_source}[/]")
#         # Train Type
#         row_items.append(model["trainType"])
#         # Model Version List
#         version_list = [
#             f"{version['version']} [dim]({version['modelVersionIdStr']})[/]"
#             for version in model["modelVersionList"]
#         ]
#         row_items.append("\n".join(version_list))
#         table.add_row(*row_items)
#     console.print(table)


# def list_evaluable_models_callback(
#     ctx: typer.Context, param: typer.CallbackParam, value: bool
# ) -> None:
#     if value:
#         print_warn_msg(
#             "This option is [bold]deprecated[/]. Use `qianfan evaluation"
#             " list-evaluable-models` instead."
#         )
#         list_evaluable_models(None, None, None)
#         raise typer.Exit()
