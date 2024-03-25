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
import logging
from datetime import datetime
from typing import Optional

from qianfan.autotuner.context import Context
from qianfan.autotuner.runner.base import Runner
from qianfan.autotuner.suggestor.base import Suggestor
from qianfan.resources.typing import Literal
from qianfan.utils.logging import Logger
from qianfan.utils.utils import uuid


class Launcher(object):
    def __init__(
        self,
        log_dir: Optional[str] = None,
        log_level: Literal["DEBUG", "INFO", "WARN", "ERROR"] = "INFO",
    ) -> None:
        self._id = uuid()
        self._logger = logging.getLogger(f"qianfan_autotuner_{self._id}")
        self._logger.setLevel(log_level)
        formatter = logging.Formatter(
            Logger._DEFAULT_MSG_FORMAT, Logger._DEFAULT_DATE_FORMAT
        )
        handler = logging.StreamHandler()
        handler.setFormatter(formatter)
        self._logger.addHandler(handler)
        if log_dir is not None:
            file_handler = logging.FileHandler(
                f"{log_dir}/qianfan_tune_{datetime.now().strftime('%Y-%m-%d_%H:%M:%S')}.log"
            )
            self._logger.addHandler(file_handler)

    async def run(self, suggestor: Suggestor, runner: Runner) -> Context:
        context = Context()

        while True:
            is_end, config_list = await suggestor.next(context)
            if is_end:
                self._logger.info("tuning finished!")
                best_config = await suggestor.best(context)
                self._logger.info(f"best config: {best_config}")
                context.set_best_result(best_config)
                break

            self._logger.info(f"turn {context.current_turn} started...")
            self._logger.info(f"suggested config list: {config_list}")
            task_list = [runner.run(config, context) for config in config_list]

            res = await asyncio.gather(*task_list)
            for config, (metrics, custom_results) in zip(config_list, res):
                self._logger.info(f"config: {config}, metrics: {metrics}")
                context.report_result(config, metrics, custom_results)
            context.next_turn()

        return context
