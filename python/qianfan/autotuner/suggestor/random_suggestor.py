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

from qianfan.autotuner.context import Context
from qianfan.autotuner.space import Categorical, Space, Uniform
from qianfan.autotuner.suggestor.base import Suggestor
from qianfan.autotuner.utils import ConfigList
from qianfan.resources.typing import Literal


class RandomSuggestor(Suggestor):
    """
    Suggestor for generating configurations randomly.

    This class randomly generates configurations within the defined search space.
    """

    def __init__(
        self,
        search_space: Dict[str, Space],
        metrics: str = "accuracy",
        mode: Literal["min", "max"] = "max",
        cost_budget: Optional[float] = None,
        cost_key: str = "total_cost",
    ) -> None:
        """
        Args:
          search_space (Dict[str, Space]):
            A dictionary defining the search space for each parameter.
          metrics (str):
            The name of the metric used for optimization. Default is "accuracy".
          mode (Literal["min", "max"]):
            The optimization mode, either "min" (minimization) or "max" (maximization).
            Default is "max".
          cost_budget (Optional[float]):
            The budget constraint on the total cost. Default is None which means the
            cost budget will not be considered.
          cost_key (str):
            The key to access the cost metric in trial results. Default is "total_cost".
        """
        super().__init__(search_space, metrics, mode)
        self.cost_budget = cost_budget
        self.cost_key = cost_key

    async def next(self, context: Context) -> Tuple[bool, ConfigList]:
        """
        Generates the next set of configurations to evaluate randomly.

        Args:
          context (Context): The context object containing the state of the autotuning
          task.

        Returns:
          Tuple[bool, ConfigList]: A tuple indicating whether the search should stop
          and the list of configurations to evaluate in the next turn.
        """
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
