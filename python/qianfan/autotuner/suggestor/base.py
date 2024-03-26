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

from typing import Dict, Tuple

from qianfan.autotuner.context import Context, TrialResult
from qianfan.autotuner.space import Space
from qianfan.autotuner.utils import Config, ConfigList


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
