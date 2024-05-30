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

from qianfan import VERSION, QfResponse
from qianfan.autotuner.context import Config, Context, Metrics
from qianfan.autotuner.runner.infer_runner import InferRunner
from qianfan.common.prompt.prompt import Prompt
from qianfan.dataset import Dataset
from qianfan.evaluation.evaluator import Evaluator
from qianfan.resources.llm.chat_completion import ChatCompletion
from qianfan.utils.utils import async_to_thread, generate_letter_num_random_id


class QianfanRunner(InferRunner):
    """
    Runner designed for running inference using Qianfan SDK.

    This class extends the InferRunner and is specifically tailored for running
    inference task using the Qianfan SDK.
    """

    def __init__(
        self,
        dataset: Dataset,
        evaluator: Evaluator,
        prompt: Optional[Prompt] = None,
        client: Optional[ChatCompletion] = None,
        repeat: int = 1,
        **kwargs: Any,
    ):
        """
        Args:
          dataset (Dataset):
            The dataset used for inference.
          evaluator (Evaluator):
            The evaluator object responsible for evaluating model outputs.
          prompt (Optional[Prompt]):
            The prompt used for inference. Default is None.
          client (Optional[ChatCompletion]):
            The client used for inference. Default is None which means the default
            client will be used.
          repeat (int):
            The number of times to repeat inference for each input. Default is 1.
          **kwargs (Any):
            Additional keyword arguments.
        """
        if client is None:
            self._client = ChatCompletion()
        else:
            self._client = client
        price_list = {
            model: (
                self._client.get_model_info(model).input_price_per_1k_tokens,
                self._client.get_model_info(model).output_price_per_1k_tokens,
            )
            for model in self._client.models()
        }

        super().__init__(dataset=dataset, price_list=price_list, **kwargs)
        self.evaluator = evaluator

        self.prompt = prompt
        self.repeat = repeat

    async def _format_prompt(
        self,
        input_list: List[List[Dict[str, Any]]],
        config: Config,
        context: Context,
    ) -> List[List[Dict[str, Any]]]:
        """
        Format the input using the prompt.
        """
        if self.prompt is not None:
            for i in range(len(input_list)):
                content = input_list[i][-1]["content"]
                new_content, _ = self.prompt.render(content=content)
                input_list[i][-1]["content"] = new_content
        return input_list

    async def _infer(self, config: Config, content: Context) -> List[Dict[str, Any]]:
        """
        Infer the whole dataset.
        """
        # TODO: self.dataset.test_using_llm()
        input_list, reference_list = self.dataset._get_input_chat_list()
        input_list = await self._format_prompt(input_list, config, content)

        results_list = []
        for _ in range(self.repeat):
            results_list.append(
                await self._client.abatch_do(
                    input_list,
                    request_id=f"qianfan_py_sdk_autotuner_v{VERSION}_{generate_letter_num_random_id()}",
                    **config,
                )
            )

        ret = []
        for i, (input, reference) in enumerate(zip(input_list, reference_list)):
            results = []
            for j in range(self.repeat):
                r = results_list[j][i]

                if isinstance(r, Exception):
                    results.append(
                        {
                            "output": None,
                            "stat": {"exception": repr(r)},
                        }
                    )
                    continue
                assert isinstance(r, QfResponse)
                results.append(
                    {
                        "output": r["result"],
                        "stat": {
                            **r["usage"],
                            **r.statistic,
                        },
                    }
                )
            ret.append({"input": input, "expect": reference, "results": results})
        return ret

    async def _evaluate(
        self,
        config: Dict[str, Any],
        result_list: List[Dict[str, Any]],
        context: Context,
    ) -> Metrics:
        """
        Evaluates the results.
        """
        sample_metrics: Dict[str, Any] = {}

        async def _eval(res: Dict[str, Any]) -> None:
            nonlocal sample_metrics
            input = res["input"]
            expect = res["expect"]
            for result in res["results"]:
                output = result["output"]
                if output is None:
                    result["metrics"] = {}
                    continue
                eval_metrics = await async_to_thread(
                    self.evaluator.evaluate, input, expect, output
                )

                if sample_metrics == {}:
                    sample_metrics = eval_metrics
                stat = result["stat"]
                stat_metrics = {}
                stat_metrics[self.completion_token_usage_key] = stat[
                    "completion_tokens"
                ]
                stat_metrics[self.prompt_token_usage_key] = stat["prompt_tokens"]
                stat_metrics[self.latency_key] = stat["total_latency"]
                result["metrics"] = {
                    **eval_metrics,
                    **stat_metrics,
                }

        await asyncio.gather(*[_eval(res) for res in result_list])

        metrics_ds = Dataset.create_from_pyobj(
            [res["metrics"] for result in result_list for res in result["results"]]
        )
        total_metrics = self.evaluator.summarize(metrics_ds)
        if total_metrics is None:
            return {}
        return total_metrics
