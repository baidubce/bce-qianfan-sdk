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

from typing import Any, Dict, List, Tuple

from qianfan.autotuner.context import Context
from qianfan.autotuner.utils import Config, Metrics
from qianfan.dataset import Dataset


class Runner(object):
    async def run(self, config: Config, context: Context) -> Tuple[Metrics, Any]:
        raise NotImplementedError()


class InferRunner(Runner):
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
        raise NotImplementedError()

    async def _evaluate(
        self,
        config: Dict[str, Any],
        result_list: List[Dict[str, Any]],
        context: Context,
    ) -> Metrics:
        raise NotImplementedError()

    async def _update_metrics(
        self,
        config: Dict[str, Any],
        result_list: List[Dict[str, Any]],
        context: Context,
        metrics: Metrics,
    ) -> Metrics:
        total_prompt_tokens = 0
        total_completion_tokens = 0
        total_req_latency = 0
        total_cost = 0
        count = 0
        model = config["model"]
        prompt_price, completion_price = self.price_list[model]
        for res in result_list:
            if res["output"] in ["", None]:
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
            "success_rate": 1.0 * count / len(result_list),
        }
        return metrics

    async def run(
        self, config: Dict[str, Any], context: Context
    ) -> Tuple[Metrics, Any]:
        res_list = await self._infer(config, context)
        # -> List[QfResponse]
        metrics = await self._evaluate(config, res_list, context)
        # -> List[QfResponse + Metrics] + TotalMetrics
        metrics = await self._update_metrics(config, res_list, context, metrics)
        # -> List[QfResponse + Metrics] + TotalMetricsUpdated
        return metrics, res_list
