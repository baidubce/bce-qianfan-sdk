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
from typing import Any, Tuple

from qianfan.autotuner.context import Context
from qianfan.autotuner.utils import Config, Metrics


class Runner(object):
    """
    Runner for evaluating configurations in an autotuning task.

    This class is the base class of runner which is responsible for evaluating
    configurations and returning metrics.
    """

    _logger: logging.Logger = logging.getLogger(__name__)

    async def run(self, config: Config, context: Context) -> Tuple[Metrics, Any]:
        """
        Runs the evaluation for a given configuration.

        Args:
          config (Config):
            The configuration to evaluate.
          context (Context):
            The context object containing the state of the autotuning task.

        Returns:
          Tuple[Metrics, Any]:
            A tuple containing the evaluated metrics and any additional results.
        """
        raise NotImplementedError()

    def _set_logger(self, logger: logging.Logger) -> None:
        """Sets the logger for this suggestor."""
        self._logger = logger
