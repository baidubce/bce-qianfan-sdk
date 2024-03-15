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

import asyncio

from qianfan.autotuner.context import Context
from qianfan.autotuner.runner.base import Runner
from qianfan.autotuner.suggestor.base import Suggestor


class Launcher(object):
    def __init__(self) -> None:
        pass

    async def run(self, suggestor: Suggestor, runner: Runner) -> Context:
        context = Context()

        while True:
            is_end, config_list = await suggestor.next(context)
            if is_end:
                best_config = await suggestor.best(context)
                context.set_best_result(best_config)
                break
            task_list = [runner.run(config, context) for config in config_list]

            res = await asyncio.gather(*task_list)
            for config, (metrics, custom_results) in zip(config_list, res):
                context.report_result(config, metrics, custom_results)
            context.next_turn()

        return context
