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

from flaml.tune.searcher.suggestion import Searcher

from qianfan.autotuner.context import Context
from qianfan.autotuner.launcher import Launcher
from qianfan.autotuner.runner.qianfan_runner import QianfanRunner
from qianfan.dataset import Dataset
from qianfan.evaluation.evaluator import Evaluator
from qianfan.extensions.flaml.autotuner.suggestor import FLAMLSuggestor
from qianfan.resources.typing import Literal


async def run(
    searcher: Searcher,
    dataset: Dataset,
    evaluator: Evaluator,
    max_turn: Optional[int] = None,
    max_time: Optional[float] = None,
    repeat: int = 1,
    log_dir: Optional[str] = None,
    log_level: Literal["DEBUG", "INFO", "WARN", "ERROR"] = "INFO",
) -> Context:
    """
    Runs the autotuning task based on flaml.

    This function orchestrates the autotuning task by coordinating the suggestor,
    runner, and evaluator.

    Args:
      searcher (Searcher):
        Searcher from flaml for suggesting configurations.
      dataset (Dataset):
        The dataset used for evaluation.
      evaluator (Evaluator):
        The evaluator object responsible for evaluating model outputs.
      max_turn (Optional[int]):
        The maximum number of turns for the autotuning task. Default is None.
      max_time (Optional[float]):
        The maximum time in seconds allowed for the autotuning task. Default is None.
      repeat (int):
        The number of times to repeat inference for each input. Default is 1.
      log_dir (Optional[str]):
        The directory to store logs. Default is None.
      log_level (Literal["DEBUG", "INFO", "WARN", "ERROR"]):
        The logging level. Default is "INFO".

    Returns:
        Context: The context object containing the results of the autotuning task.
    """
    return await Launcher(
        log_dir=log_dir,
        log_level=log_level,
        max_turn=max_turn,
        max_time=max_time,
    ).run(
        suggestor=FLAMLSuggestor(searcher),
        runner=QianfanRunner(
            dataset=dataset,
            evaluator=evaluator,
            repeat=repeat,  # 重复推理次数，用于减少大模型输出随机性对结果准确性的干扰
        ),
    )
