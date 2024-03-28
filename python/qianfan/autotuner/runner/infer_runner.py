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

import time
from typing import Any, Dict, List, Tuple

from qianfan.autotuner.context import Context
from qianfan.autotuner.runner.base import Runner
from qianfan.autotuner.utils import Metrics
from qianfan.dataset import Dataset


class InferRunner(Runner):
    """
    Base runner class for inference tasks.

    This class is the base class of runner specifically tailored for inference tasks.
    This class will automatically infer the dataset, evaluate the inference result and
    calculate the metrics such as cost, latency and so on. The derived class only needs
    to implment the `_infer` and `_evaluate` methods.


    """

    def __init__(
        self,
        dataset: Dataset,
        price_list: Dict[str, Tuple[float, float]],
        cost_key: str = "cost",
        prompt_token_usage_key: str = "prompt_tokens",
        completion_token_usage_key: str = "completion_tokens",
        latency_key: str = "latency",
        **kwargs: Any,
    ) -> None:
        """
        Args:
          dataset (Dataset):
            The dataset used for inference and evaluation.
          price_list (Dict[str, Tuple[float, float]]):
            A dictionary mapping model names to their corresponding price ranges.
          cost_key (str):
            The key to access the cost metric in the result of each output. Default
            is "cost".
          prompt_token_usage_key (str):
            The key to access prompt token usage metric in the result of each output.
            Default is "prompt_tokens".
          completion_token_usage_key (str):
            The key to access completion token usage metric in trial results. Default
            is "completion_tokens".
          latency_key (str):
            The key to access the latency metric in trial results. Default is "latency".
          **kwargs (Any):
            Additional keyword arguments.
        """
        super().__init__()
        self.dataset = dataset
        self.price_list = price_list
        self.cost_key = cost_key
        self.prompt_token_usage_key = prompt_token_usage_key
        self.completion_token_usage_key = completion_token_usage_key
        self.latency_key = latency_key

    async def _infer(
        self, config: Dict[str, Any], context: Context
    ) -> List[Dict[str, Any]]:
        """
        Infer the dataset using the given config.
        """
        raise NotImplementedError()

    async def _evaluate(
        self,
        config: Dict[str, Any],
        result_list: List[Dict[str, Any]],
        context: Context,
    ) -> Metrics:
        """
        Evaluate the inference result and return the metrics.
        """
        raise NotImplementedError()

    async def _update_metrics(
        self,
        config: Dict[str, Any],
        result_list: List[Dict[str, Any]],
        context: Context,
        metrics: Metrics,
    ) -> Metrics:
        """
        Calcuate the general metrics.
        """
        total_prompt_tokens = 0
        total_completion_tokens = 0
        total_req_latency = 0
        total_cost = 0
        count = 0
        model = config["model"]
        if model not in self.price_list:
            self._logger.warn(f"{model} is not in the price list, 0 cost will be used.")
        prompt_price, completion_price = self.price_list.get(model, (0, 0))
        for item in result_list:
            for res in item["results"]:
                if res["output"] is None:
                    continue
                count += 1
                stat = res["metrics"]
                prompt_token = stat.get(self.prompt_token_usage_key, 0)
                completion_token = stat.get(self.completion_token_usage_key, 0)
                total_prompt_tokens += prompt_token
                total_completion_tokens += completion_token
                total_req_latency += stat.get(self.latency_key, 0)
                cost = (
                    prompt_token * prompt_price + completion_token * completion_price
                ) / 1000
                res["metrics"]["cost"] = cost
                total_cost += cost

        metrics = {
            **metrics,
            "avg_prompt_tokens": total_prompt_tokens / count,
            "avg_completion_tokens": total_completion_tokens / count,
            "avg_total_tokens": (total_prompt_tokens + total_completion_tokens) / count,
            "avg_req_latency": total_req_latency / count,
            "avg_tokens_per_second": (
                total_prompt_tokens + total_completion_tokens
            ) / total_req_latency,
            "avg_cost": total_cost / count,
            "total_cost": total_cost,
            "success_rate": (
                1.0 * count / len(result_list) / len(result_list[0]["results"])
            ),
        }
        return metrics

    async def run(
        self, config: Dict[str, Any], context: Context
    ) -> Tuple[Metrics, Any]:
        """
        Run the inference and evaluate the result.
        """
        start_time = time.time()
        # infer the whole dataset
        res_list = await self._infer(config, context)
        # evaluate the result
        metrics = await self._evaluate(config, res_list, context)
        # calcuate the general metrics
        metrics = await self._update_metrics(config, res_list, context, metrics)
        # return the metrics and inference result
        metrics["total_time"] = time.time() - start_time
        return metrics, res_list
