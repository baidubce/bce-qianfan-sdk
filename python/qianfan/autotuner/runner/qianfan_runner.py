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
from typing import Any, Dict, List, Optional

import qianfan
from qianfan import QfResponse
from qianfan.autotuner.context import Config, Context, Metrics
from qianfan.autotuner.runner.base import InferRunner
from qianfan.common.prompt.prompt import Prompt
from qianfan.dataset import Dataset
from qianfan.evaluation.evaluator import Evaluator
from qianfan.utils.utils import async_to_thread

price_list = {
    "ERNIE-Bot-turbo": (0.008, 0.008),
    "ERNIE-Bot": (0.012, 0.012),
    "ERNIE-Bot-4": (0.12, 0.12),
    "ERNIE-Speed": (0.004, 0.008),
    "BLOOMZ-7B": (0.004, 0.004),
    "Qianfan-Chinese-Llama-2-7B": (0.004, 0.004),
    "ChatGLM2-6B-32K": (0.004, 0.004),
    "Qianfan-Chinese-Llama-2-13B": (0.006, 0.006),
    "Mixtral-8x7B-Instruct": (0.035, 0.035),
    "Llama-2-13b-chat": (0.006, 0.006),
}


class QianfanRunner(InferRunner):
    def __init__(
        self,
        dataset: Dataset,
        evaluator: Evaluator,
        prompt: Optional[Prompt] = None,
        **kwargs: Any
    ):
        super().__init__(dataset=dataset, price_list=price_list, **kwargs)
        self.evaluator = evaluator
        self._client = qianfan.ChatCompletion()
        self.prompt = prompt

    async def _format_prompt(
        self,
        input_list: List[List[Dict[str, Any]]],
        config: Config,
        context: Context,
    ) -> List[List[Dict[str, Any]]]:
        if self.prompt is not None:
            for i in range(len(input_list)):
                content = input_list[i][-1]["content"]
                new_content = self.prompt.render(content=content)
                input_list[i][-1]["content"] = new_content
        return input_list

    async def _infer(self, config: Config, content: Context) -> List[Dict[str, Any]]:
        # TODO: self.dataset.test_using_llm()
        input_list, reference_list = self.dataset._get_input_chat_list()
        input_list = await self._format_prompt(input_list, config, content)

        res = await self._client.abatch_do(input_list, **config)
        ret = []
        for r, input, reference in zip(res, input_list, reference_list):
            assert isinstance(r, QfResponse)
            ret.append(
                {
                    "input": input,
                    "expect": reference,
                    "output": r["result"],
                    "stat": {
                        **r["usage"],
                        **r.statistic,
                    },
                }
            )
        return ret

    async def _evaluate(
        self,
        config: Dict[str, Any],
        result_list: List[Dict[str, Any]],
        context: Context,
    ) -> Metrics:
        sample_metrics: Dict[str, Any] = {}

        async def _eval(res: Dict[str, Any]) -> None:
            nonlocal sample_metrics
            input = res["input"]
            output = res["output"]
            expect = res["expect"]
            eval_metrics = await async_to_thread(
                self.evaluator.evaluate, input, expect, output
            )

            if sample_metrics == {}:
                sample_metrics = eval_metrics
            stat = res["stat"]
            stat_metrics = {}
            stat_metrics[self.completion_token_usage_key] = stat["completion_tokens"]
            stat_metrics[self.prompt_token_usage_key] = stat["prompt_tokens"]
            stat_metrics[self.latency_key] = stat["total_latency"]
            res["metrics"] = {
                **eval_metrics,
                **stat_metrics,
            }

        await asyncio.gather(*[_eval(res) for res in result_list])

        total_metrics = {
            k: 0.0
            for k in sample_metrics
            if isinstance(sample_metrics[k], (float, int))
        }
        for item in result_list:
            for k in total_metrics:
                total_metrics[k] += item["metrics"][k]
        for k, v in total_metrics.items():
            total_metrics[k] = v / len(result_list)

        return total_metrics
