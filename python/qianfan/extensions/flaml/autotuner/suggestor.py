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

from typing import Any, Tuple

from flaml.tune.searcher.suggestion import Searcher

from qianfan.autotuner.context import Context
from qianfan.autotuner.suggestor.base import Suggestor
from qianfan.autotuner.utils import ConfigList


class FLAMLSuggestor(Suggestor):
    def __init__(self, searcher: Searcher, **kwargs: Any) -> None:
        super().__init__({}, searcher._metric, searcher._mode, **kwargs)
        self.searcher = searcher

    async def next(self, context: Context) -> Tuple[bool, ConfigList]:
        history = context.history
        if len(history) > 1:
            metrics = history[-2][0].metrics
            metrics["training_iteration"] = len(history) - 2
            self.searcher.on_trial_result(
                f"trial_{len(history) - 1}", history[-2][-1].metrics
            )
            self.searcher.on_trial_complete(
                f"trial_{len(history) - 1}",
                {"config": history[-2][-1].config, **history[-2][-1].metrics},
            )
        config = self.searcher.suggest(f"trial_{len(history)}")
        if config is None:
            return True, []
        return False, [config]
