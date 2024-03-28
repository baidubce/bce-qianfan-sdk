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

from typing import Dict, Optional

from qianfan.autotuner.context import Context
from qianfan.autotuner.launcher import Launcher
from qianfan.autotuner.runner.qianfan_runner import QianfanRunner
from qianfan.autotuner.space import Space
from qianfan.autotuner.suggestor.base import Suggestor
from qianfan.autotuner.suggestor.random_suggestor import RandomSuggestor
from qianfan.dataset import Dataset
from qianfan.evaluation.evaluator import Evaluator
from qianfan.resources.typing import Literal


async def run(
    search_space: Dict[str, Space],
    dataset: Dataset,
    evaluator: Evaluator,
    suggestor: Literal["random"] = "random",
    cost_budget: Optional[float] = None,
    metrics: str = "score",
    mode: Literal["min", "max"] = "max",
    max_turn: Optional[int] = None,
    repeat: int = 1,
    log_dir: Optional[str] = None,
    log_level: Literal["DEBUG", "INFO", "WARN", "ERROR"] = "INFO",
) -> Context:
    _suggestor: Suggestor
    if suggestor == "random":
        _suggestor = RandomSuggestor(
            search_space=search_space,
            cost_budget=cost_budget,  # 设定整个流程的预算
            metrics=metrics,  # 设定评估指标字段，与 Evaluator 输出对应
            mode=mode,  # 设定评估指标最大化还是最小化
        )
    else:
        raise NotImplementedError(f"Unsupported suggestor: {suggestor}")
    return await Launcher(
        log_dir=log_dir,
        log_level=log_level,
        max_turn=max_turn,
    ).run(
        suggestor=_suggestor,
        runner=QianfanRunner(
            dataset=dataset,
            evaluator=evaluator,
            repeat=repeat,  # 重复推理次数，用于减少大模型输出随机性对结果准确性的干扰
        ),
    )
