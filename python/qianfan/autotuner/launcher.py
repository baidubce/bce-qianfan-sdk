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
import time
from datetime import datetime
from typing import Optional

from qianfan.autotuner.context import Context
from qianfan.autotuner.runner.base import Runner
from qianfan.autotuner.suggestor.base import Suggestor
from qianfan.resources.typing import Literal
from qianfan.utils.logging import Logger
from qianfan.utils.utils import uuid


class Launcher(object):
    """
    Launcher of an autotuning task.
    """

    def __init__(
        self,
        log_dir: Optional[str] = None,
        log_level: Literal["DEBUG", "INFO", "WARN", "ERROR"] = "INFO",
        max_turn: Optional[int] = None,
        max_time: Optional[float] = None,
    ) -> None:
        """
        Args:
          log_dir (Optional[str]):
            The directory to store logs. Default is None which means no log will
            be stored.
          log_level (Literal["DEBUG", "INFO", "WARN", "ERROR"]):
            The logging level. Default is "INFO".
        """
        self._id = uuid()
        self._max_turn = max_turn
        self._max_time = max_time
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
            file_handler.setFormatter(formatter)
            self._logger.addHandler(file_handler)

    async def run(self, suggestor: Suggestor, runner: Runner) -> Context:
        """
        Runs the autotuning task asynchronously.

        This method executes the autotuning task asynchronously using the provided
        suggestor and runner.

        Args:
          suggestor (Suggestor):
            The suggestor object responsible for generating configurations.
          runner (Runner):
            The runner object responsible for evaluating configurations.

        Returns:
            Context: The context object containing the results of the autotuning task.
        """
        context = Context()
        suggestor._set_logger(self._logger)
        runner._set_logger(self._logger)
        start_time = time.time()

        while True:
            is_end = False
            cur_time = time.time()
            if self._max_turn is not None and context.current_turn == self._max_turn:
                self._logger.info(f"max turn reached: {self._max_turn}")
                is_end = True
            elif self._max_time is not None and cur_time - start_time > self._max_time:
                self._logger.info(
                    f"max time reached: {cur_time - start_time} seconds elapsed..."
                )
                is_end = True
            else:
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
