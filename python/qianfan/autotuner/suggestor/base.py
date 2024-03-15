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

import random
from typing import Dict, Optional, Tuple

from qianfan.autotuner.context import Context, TrialResult
from qianfan.autotuner.space import Categorical, Space, Uniform
from qianfan.autotuner.utils import Config, ConfigList
from qianfan.resources.typing import Literal


class Suggestor(object):
    def __init__(
        self, search_space: Dict[str, Space], metrics: str = "score", mode: str = "max"
    ) -> None:
        self.search_space = search_space
        self.metrics = metrics
        self.mode = mode

    async def next(self, context: Context) -> Tuple[bool, ConfigList]:
        raise NotImplementedError()

    async def best(self, context: Context) -> Config:
        raise NotImplementedError()


class RandomSuggestor(Suggestor):
    def __init__(
        self,
        search_space: Dict[str, Space],
        metrics: str = "accuracy",
        mode: Literal["min", "max"] = "max",
        cost_budget: Optional[float] = None,
        cost_key: str = "total_cost",
    ) -> None:
        super().__init__(search_space, metrics, mode)
        self.cost_budget = cost_budget
        self.cost_key = cost_key

    async def next(self, context: Context) -> Tuple[bool, ConfigList]:
        if self.cost_budget is not None:
            total_cost = 0
            for turn in context.history:
                for trial in turn:
                    total_cost += trial.metrics[self.cost_key]
            if total_cost > self.cost_budget:
                return True, []

        config = {}
        for k, space in self.search_space.items():
            if isinstance(space, Uniform):
                value = random.uniform(space.low, space.high)
            elif isinstance(space, Categorical):
                value = random.choice(space.choices)
            else:
                raise NotImplementedError("Unsupported space type")
            config[k] = value

        return False, [config]

    async def best(self, context: Context) -> Config:
        def compare(trial: TrialResult, best: TrialResult) -> bool:
            if self.mode == "max":
                return trial.metrics[self.metrics] > best.metrics[self.metrics]
            if self.mode == "min":
                return trial.metrics[self.metrics] < best.metrics[self.metrics]
            raise NotImplementedError("Unsupported mode")

        best = None
        for turn in context.history:
            for trial in turn:
                if best is None or compare(trial, best):
                    best = trial
        if best is None:
            raise RuntimeError("No trial history found.")
        return best.config
