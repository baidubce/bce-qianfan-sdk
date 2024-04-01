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

from typing import Any, List, Optional

from qianfan.autotuner.utils import Config, Metrics, TrialResult


class Context(object):
    """
    Context for managing the state of an autotuning task.

    This class manages the state of an autotuning task including the current turn,
    historical data, and the best configuration found.

    Attributes:
      current_turn (int):
        The current turn of the autotuning task.
      history (List[List[TrialResult]]):
        A list containing the history of trial results for each turn.
      best (Optional[Config]):
        The best configuration found during the autotuning task.
    """

    def __init__(self) -> None:
        self.current_turn: int = 0
        self.history: List[List[TrialResult]] = [[]]
        self.best: Optional[Config] = None

    def set_best_result(self, config: Config) -> None:
        """
        Sets the best configuration found.

        Args:
            config (Config): The best configuration found.
        """
        self.best = config

    def next_turn(self) -> None:
        """Moves to the next turn of the autotuning task."""
        self.current_turn += 1
        self.history.append([])

    def report_result(
        self,
        config: Config,
        metrics: Metrics,
        custom_results: Any = None,
    ) -> None:
        """
        Reports the result of a trial.

        Args:
            config (Config): The configuration used for the trial.
            metrics (Metrics): The metrics obtained from the trial.
            custom_results (Any): Customized results from the trial, if any.
        """
        self.history[-1].append(
            TrialResult(
                turn=self.current_turn,
                config=config,
                metrics=metrics,
                custom_results=custom_results,
            )
        )
