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

import logging
from typing import Dict, Tuple

from qianfan.autotuner.context import Context, TrialResult
from qianfan.autotuner.space import Space
from qianfan.autotuner.utils import Config, ConfigList


class Suggestor(object):
    """
    Suggestor for generating configurations in an autotuning task based on a
    search space and historical data..

    This class is the base class for all suggestors.
    """

    def __init__(
        self, search_space: Dict[str, Space], metrics: str = "score", mode: str = "max"
    ) -> None:
        """
        Args:
          search_space (Dict[str, Space]):
            A dictionary defining the search space for each parameter.
          metrics (str):
            The name of the metric used for optimization. Default is "score".
          mode (str):
            The optimization mode, either "max" (maximization) or "min" (minimization).
            Default is "max".
        """
        self.search_space = search_space
        self.metrics = metrics
        self.mode = mode
        self._logger = logging.getLogger(__name__)

    async def next(self, context: Context) -> Tuple[bool, ConfigList]:
        """
        Generates the next set of configurations to evaluate.

        Args:
          context (Context): The context object containing the state of the
          autotuning task.

        Returns:
          Tuple[bool, ConfigList]: A tuple indicating whether the search should stop
          and the list of configurations to evaluate in the next turn.
        """
        raise NotImplementedError()

    async def best(self, context: Context) -> Config:
        """
        Determines the best configuration found based on historical data.

        Args:
          context (Context):
            The context object containing the state of the autotuning task.

        Returns:
          Config: The best configuration found.
        """

        def compare(trial: TrialResult, best: TrialResult) -> bool:
            """Compares two trial results based on the optimization mode."""
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

    def _set_logger(self, logger: logging.Logger) -> None:
        """Sets the logger for this suggestor."""
        self._logger = logger
