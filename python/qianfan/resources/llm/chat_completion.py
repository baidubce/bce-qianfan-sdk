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
import copy
from functools import partial
from typing import (
    Any,
    AsyncIterator,
    Callable,
    Dict,
    Iterator,
    List,
    Optional,
    Tuple,
    Type,
    Union,
)

import qianfan.errors as errors
from qianfan.consts import DefaultLLMModel, DefaultValue
from qianfan.resources.llm.base import (
    UNSPECIFIED_MODEL,
    BaseResourceV1,
    BaseResourceV2,
    BatchRequestFuture,
    VersionBase,
)
from qianfan.resources.llm.function import Function, FunctionV2
from qianfan.resources.tools.tokenizer import Tokenizer
from qianfan.resources.typing import JsonBody, QfLLMInfo, QfMessages, QfResponse, QfRole
from qianfan.resources.typing_client import Completion, CompletionChunk
from qianfan.utils.logging import log_error, log_info, log_warn


class _ChatCompletionV1(BaseResourceV1):
    """
    QianFan ChatCompletion is an agent for calling QianFan ChatCompletion API.
    """

    def _local_models(self) -> Dict[str, QfLLMInfo]:
        info_list = {
            "ERNIE-4.0-8K-Latest": QfLLMInfo(
                endpoint="/chat/ernie-4.0-8k-latest",
                required_keys={"messages"},
                optional_keys={
                    "stream",
                    "temperature",
                    "top_p",
                    "penalty_score",
                    "user_id",
                    "system",
                    "stop",
                    "enable_system_memory",
                    "system_memory_id",
                    "disable_search",
                    "enable_citation",
                    "enable_trace",
                    "max_output_tokens",
                    "response_format",
                },
                max_input_chars=20000,
                max_input_tokens=5120,
                input_price_per_1k_tokens=0.12,
                output_price_per_1k_tokens=0.12,
            ),
            "ERNIE-4.0-8K-0613": QfLLMInfo(
                endpoint="/chat/ernie-4.0-8k-0613",
                required_keys={"messages"},
                optional_keys={
                    "stream",
                    "temperature",
                    "top_p",
                    "penalty_score",
                    "user_id",
                    "system",
                    "stop",
                    "enable_system_memory",
                    "system_memory_id",
                    "disable_search",
                    "enable_citation",
                    "enable_trace",
                    "max_output_tokens",
                    "response_format",
                },
                max_input_chars=20000,
                max_input_tokens=5120,
                input_price_per_1k_tokens=0.12,
                output_price_per_1k_tokens=0.12,
            ),
            "ERNIE-4.0-Turbo-8K": QfLLMInfo(
                endpoint="/chat/ernie-4.0-turbo-8k",
                required_keys={"messages"},
                optional_keys={
                    "stream",
                    "temperature",
                    "top_p",
                    "penalty_score",
                    "user_id",
                    "system",
                    "stop",
                    "enable_system_memory",
                    "system_memory_id",
                    "disable_search",
                    "enable_citation",
                    "enable_trace",
                    "max_output_tokens",
                    "response_format",
                },
                max_input_chars=20000,
                max_input_tokens=5120,
                input_price_per_1k_tokens=0.12,
                output_price_per_1k_tokens=0.12,
            ),
            "ERNIE-Lite-AppBuilder-8K-0614": QfLLMInfo(
                endpoint="/chat/ai_apaas_lite",
                required_keys={"messages"},
                optional_keys={
                    "stream",
                    "temperature",
                    "top_p",
                    "penalty_score",
                    "system",
                    "user_id",
                    "tools",
                    "tool_choice",
                    "max_output_tokens",
                    "min_output_tokens",
                    "frequency_penalty",
                    "presence_penalty",
                },
                max_input_chars=11200,
                max_input_tokens=7168,
                input_price_per_1k_tokens=0.004,
                output_price_per_1k_tokens=0.008,
            ),
            "ERNIE-3.5-8K-0701": QfLLMInfo(
                endpoint="/chat/ernie-3.5-8k-0701",
                required_keys={"messages"},
                optional_keys={
                    "stream",
                    "temperature",
                    "top_p",
                    "penalty_score",
                    "user_id",
                    "system",
                    "stop",
                    "enable_system_memory",
                    "system_memory_id",
                    "disable_search",
                    "enable_citation",
                    "enable_trace",
                    "max_output_tokens",
                    "response_format",
                    "functions",
                    "tool_choice",
                },
                max_input_chars=20000,
                max_input_tokens=5120,
                input_price_per_1k_tokens=0.12,
                output_price_per_1k_tokens=0.12,
            ),
            "ERNIE-3.5-8K-0613": QfLLMInfo(
                endpoint="/chat/ernie-3.5-8k-0613",
                required_keys={"messages"},
                optional_keys={
                    "stream",
                    "temperature",
                    "top_p",
                    "penalty_score",
                    "user_id",
                    "system",
                    "stop",
                    "enable_system_memory",
                    "system_memory_id",
                    "disable_search",
                    "enable_citation",
                    "enable_trace",
                    "max_output_tokens",
                    "response_format",
                    "functions",
                    "tool_choice",
                },
                max_input_chars=20000,
                max_input_tokens=5120,
                input_price_per_1k_tokens=0.012,
                output_price_per_1k_tokens=0.012,
            ),
            "ERNIE-Lite-Pro-8K": QfLLMInfo(
                endpoint="/chat/ernie-lite-pro-8k",
                required_keys={"messages"},
                optional_keys={
                    "stream",
                    "temperature",
                    "top_p",
                    "penalty_score",
                    "user_id",
                    "tools",
                    "tool_choice",
                    "system",
                    "stop",
                },
                max_input_chars=24000,
                max_input_tokens=6144,
                input_price_per_1k_tokens=0.008,
                output_price_per_1k_tokens=0.008,
            ),
            "ERNIE-Lite-8K-0922": QfLLMInfo(
                endpoint="/chat/eb-instant",
                required_keys={"messages"},
                optional_keys={
                    "stream",
                    "temperature",
                    "top_p",
                    "penalty_score",
                    "user_id",
                    "tools",
                    "tool_choice",
                    "system",
                    "stop",
                },
                max_input_chars=11200,
                max_input_tokens=7168,
                input_price_per_1k_tokens=0.008,
                output_price_per_1k_tokens=0.008,
            ),
            "ERNIE-Lite-8K-0308": QfLLMInfo(
                endpoint="/chat/ernie-lite-8k",
                required_keys={"messages"},
                optional_keys={
                    "stream",
                    "temperature",
                    "top_p",
                    "penalty_score",
                    "user_id",
                    "system",
                    "stop",
                    "max_output_tokens",
                    "min_output_tokens",
                    "frequency_penalty",
                    "presence_penalty",
                },
                max_input_chars=11200,
                max_input_tokens=7168,
                input_price_per_1k_tokens=0.003,
                output_price_per_1k_tokens=0.006,
            ),
            "ERNIE-Lite-V": QfLLMInfo(
                endpoint="/chat/ernie-lite-v",
                required_keys={"messages"},
                optional_keys={
                    "stream",
                    "temperature",
                    "top_p",
                    "penalty_score",
                    "user_id",
                    "system",
                    "stop",
                    "max_output_tokens",
                    "min_output_tokens",
                    "frequency_penalty",
                    "presence_penalty",
                },
                max_input_chars=11200,
                max_input_tokens=7168,
                input_price_per_1k_tokens=0.003,
                output_price_per_1k_tokens=0.006,
            ),
            "ERNIE-3.5-8K": QfLLMInfo(
                endpoint="/chat/completions",
                required_keys={"messages"},
                optional_keys={
                    "stream",
                    "temperature",
                    "top_p",
                    "penalty_score",
                    "functions",
                    "system",
                    "user_id",
                    "user_setting",
                    "stop",
                    "disable_search",
                    "enable_citation",
                    "max_output_tokens",
                    "response_format",
                    "tool_choice",
                    "enable_trace",
                    "enable_system_memory",
                    "system_memory_id",
                },
                max_input_chars=20000,
                max_input_tokens=5120,
                input_price_per_1k_tokens=0.012,
                output_price_per_1k_tokens=0.012,
            ),
            "ERNIE-4.0-8K": QfLLMInfo(
                endpoint="/chat/completions_pro",
                required_keys={"messages"},
                optional_keys={
                    "stream",
                    "temperature",
                    "top_p",
                    "penalty_score",
                    "functions",
                    "system",
                    "user_id",
                    "stop",
                    "disable_search",
                    "enable_citation",
                    "response_format",
                    "max_output_tokens",
                    "enable_trace",
                    "enable_system_memory",
                    "system_memory_id",
                },
                max_input_chars=20000,
                max_input_tokens=5120,
                input_price_per_1k_tokens=0.12,
                output_price_per_1k_tokens=0.12,
            ),
            "ERNIE-4.0-8K-0329": QfLLMInfo(
                endpoint="/chat/ernie-4.0-8k-0329",
                required_keys={"messages"},
                optional_keys={
                    "stream",
                    "temperature",
                    "top_p",
                    "penalty_score",
                    "functions",
                    "system",
                    "user_id",
                    "stop",
                    "disable_search",
                    "enable_citation",
                    "response_format",
                    "max_output_tokens",
                    "enable_trace",
                    "enable_system_memory",
                    "system_memory_id",
                },
                max_input_chars=20000,
                max_input_tokens=5120,
                input_price_per_1k_tokens=0.12,
                output_price_per_1k_tokens=0.12,
            ),
            "ERNIE-4.0-8K-0104": QfLLMInfo(
                endpoint="/chat/ernie-4.0-8k-0104",
                required_keys={"messages"},
                optional_keys={
                    "stream",
                    "temperature",
                    "top_p",
                    "penalty_score",
                    "functions",
                    "system",
                    "user_id",
                    "stop",
                    "disable_search",
                    "enable_citation",
                    "response_format",
                    "max_output_tokens",
                    "enable_trace",
                    "enable_system_memory",
                    "system_memory_id",
                },
                max_input_chars=20000,
                max_input_tokens=5120,
                input_price_per_1k_tokens=0.12,
                output_price_per_1k_tokens=0.12,
            ),
            "ERNIE-4.0-8K-Preview-0518": QfLLMInfo(
                endpoint="/chat/completions_adv_pro",
                required_keys={"messages"},
                optional_keys={
                    "stream",
                    "temperature",
                    "top_p",
                    "penalty_score",
                    "functions",
                    "system",
                    "user_id",
                    "stop",
                    "disable_search",
                    "enable_citation",
                    "response_format",
                    "max_output_tokens",
                    "enable_trace",
                    "enable_system_memory",
                    "system_memory_id",
                },
                max_input_chars=20000,
                max_input_tokens=5120,
                input_price_per_1k_tokens=0.12,
                output_price_per_1k_tokens=0.12,
            ),
            "ERNIE-4.0-8K-preview": QfLLMInfo(
                endpoint="/chat/ernie-4.0-8k-preview",
                required_keys={"messages"},
                optional_keys={
                    "stream",
                    "temperature",
                    "top_p",
                    "penalty_score",
                    "functions",
                    "system",
                    "user_id",
                    "stop",
                    "disable_search",
                    "enable_citation",
                    "response_format",
                    "max_output_tokens",
                    "enable_trace",
                    "enable_system_memory",
                    "system_memory_id",
                },
                max_input_chars=20000,
                max_input_tokens=5120,
                input_price_per_1k_tokens=0.12,
                output_price_per_1k_tokens=0.12,
            ),
            "ERNIE-3.5-128K": QfLLMInfo(
                endpoint="/chat/ernie-3.5-128k",
                required_keys={"messages"},
                optional_keys={
                    "stream",
                    "temperature",
                    "top_p",
                    "penalty_score",
                    "functions",
                    "system",
                    "user_id",
                    "user_setting",
                    "stop",
                    "disable_search",
                    "enable_citation",
                    "max_output_tokens",
                    "response_format",
                    "tool_choice",
                    "enable_trace",
                    "enable_system_memory",
                    "system_memory_id",
                },
                max_input_chars=516096,
                max_input_tokens=126976,
                input_price_per_1k_tokens=0.012,
                output_price_per_1k_tokens=0.012,
            ),
            "ERNIE-3.5-8K-preview": QfLLMInfo(
                endpoint="/chat/ernie-3.5-8k-preview",
                required_keys={"messages"},
                optional_keys={
                    "stream",
                    "temperature",
                    "top_p",
                    "penalty_score",
                    "functions",
                    "system",
                    "user_id",
                    "user_setting",
                    "stop",
                    "disable_search",
                    "enable_citation",
                    "max_output_tokens",
                    "response_format",
                    "tool_choice",
                    "enable_trace",
                    "enable_system_memory",
                    "system_memory_id",
                },
                max_input_chars=20000,
                max_input_tokens=5120,
                input_price_per_1k_tokens=0.024,
                output_price_per_1k_tokens=0.048,
            ),
            "ERNIE-3.5-8K-0205": QfLLMInfo(
                endpoint="/chat/ernie-3.5-8k-0205",
                required_keys={"messages"},
                optional_keys={
                    "stream",
                    "temperature",
                    "top_p",
                    "penalty_score",
                    "functions",
                    "system",
                    "user_id",
                    "user_setting",
                    "stop",
                    "disable_search",
                    "enable_citation",
                    "max_output_tokens",
                    "response_format",
                    "tool_choice",
                    "enable_trace",
                    "enable_system_memory",
                    "system_memory_id",
                },
                max_input_chars=20000,
                max_input_tokens=5120,
                input_price_per_1k_tokens=0.024,
                output_price_per_1k_tokens=0.048,
            ),
            "ERNIE-3.5-8K-0329": QfLLMInfo(
                endpoint="/chat/ernie-3.5-8k-0329",
                required_keys={"messages"},
                optional_keys={
                    "stream",
                    "temperature",
                    "top_p",
                    "penalty_score",
                    "functions",
                    "system",
                    "user_id",
                    "user_setting",
                    "stop",
                    "disable_search",
                    "enable_citation",
                    "max_output_tokens",
                    "response_format",
                    "tool_choice",
                    "enable_trace",
                    "enable_system_memory",
                    "system_memory_id",
                },
                max_input_chars=8000,
                max_input_tokens=2048,
                input_price_per_1k_tokens=0.012,
                output_price_per_1k_tokens=0.012,
            ),
            "ERNIE-Speed-Pro-8K": QfLLMInfo(
                endpoint="/chat/ernie-speed-pro-8k",
                required_keys={"messages"},
                optional_keys={
                    "stream",
                    "temperature",
                    "top_p",
                    "penalty_score",
                    "user_id",
                    "tools",
                    "tool_choice",
                    "system",
                    "stop",
                    "max_output_tokens",
                    "min_output_tokens",
                    "frequency_penalty",
                    "presence_penalty",
                },
                max_input_chars=24000,
                max_input_tokens=6144,
                input_price_per_1k_tokens=0.004,
                output_price_per_1k_tokens=0.008,
            ),
            "ERNIE-Speed-8K": QfLLMInfo(
                endpoint="/chat/ernie_speed",
                required_keys={"messages"},
                optional_keys={
                    "stream",
                    "temperature",
                    "top_p",
                    "penalty_score",
                    "user_id",
                    "tools",
                    "tool_choice",
                    "system",
                    "stop",
                    "max_output_tokens",
                    "min_output_tokens",
                    "frequency_penalty",
                    "presence_penalty",
                },
                max_input_chars=11200,
                max_input_tokens=7168,
                input_price_per_1k_tokens=0.004,
                output_price_per_1k_tokens=0.008,
            ),
            "ERNIE-Speed-Pro-128K": QfLLMInfo(
                endpoint="/chat/ernie-speed-pro-128k",
                required_keys={"messages"},
                optional_keys={
                    "stream",
                    "temperature",
                    "top_p",
                    "penalty_score",
                    "user_id",
                    "tools",
                    "tool_choice",
                    "system",
                    "stop",
                    "max_output_tokens",
                    "frequency_penalty",
                    "presence_penalty",
                },
                max_input_chars=516096,
                max_input_tokens=126976,
                input_price_per_1k_tokens=0.004,
                output_price_per_1k_tokens=0.008,
            ),
            "ERNIE-Speed-128K": QfLLMInfo(
                endpoint="/chat/ernie-speed-128k",
                required_keys={"messages"},
                optional_keys={
                    "stream",
                    "temperature",
                    "top_p",
                    "penalty_score",
                    "user_id",
                    "tools",
                    "tool_choice",
                    "system",
                    "stop",
                    "max_output_tokens",
                    "frequency_penalty",
                    "presence_penalty",
                },
                max_input_chars=507904,
                max_input_tokens=126976,
                input_price_per_1k_tokens=0.004,
                output_price_per_1k_tokens=0.008,
            ),
            "ERNIE Speed-AppBuilder": QfLLMInfo(
                endpoint="/chat/ai_apaas",
                required_keys={"messages"},
                optional_keys={
                    "stream",
                    "temperature",
                    "top_p",
                    "penalty_score",
                    "system",
                    "user_id",
                    "tools",
                    "tool_choice",
                },
                max_input_chars=11200,
                max_input_tokens=7168,
                input_price_per_1k_tokens=0.004,
                output_price_per_1k_tokens=0.008,
            ),
            "ERNIE-Tiny-8K": QfLLMInfo(
                endpoint="/chat/ernie-tiny-8k",
                required_keys={"messages"},
                optional_keys={
                    "stream",
                    "temperature",
                    "top_p",
                    "penalty_score",
                    "user_id",
                    "tools",
                    "tool_choice",
                    "system",
                    "stop",
                    "max_output_tokens",
                    "min_output_tokens",
                    "frequency_penalty",
                    "presence_penalty",
                },
                max_input_chars=24000,
                max_input_tokens=6144,
                input_price_per_1k_tokens=0.001,
                output_price_per_1k_tokens=0.001,
            ),
            "ERNIE-Novel-8K": QfLLMInfo(
                endpoint="/chat/ernie-novel-8k",
                required_keys={"messages"},
                optional_keys={
                    "stream",
                    "temperature",
                    "top_p",
                    "penalty_score",
                    "user_id",
                    "tools",
                    "tool_choice",
                    "system",
                    "stop",
                    "enable_system_memory",
                    "system_memory_id",
                    "max_output_tokens",
                    "min_output_tokens",
                    "frequency_penalty",
                    "presence_penalty",
                },
                max_input_chars=24000,
                max_input_tokens=6144,
                input_price_per_1k_tokens=0.001,
                output_price_per_1k_tokens=0.001,
            ),
            "ERNIE-Function-8K": QfLLMInfo(
                endpoint="/chat/ernie-func-8k",
                required_keys={"messages"},
                optional_keys={
                    "stream",
                    "temperature",
                    "top_p",
                    "penalty_score",
                    "system",
                    "user_id",
                    "stop",
                    "max_output_tokens",
                },
                max_input_chars=24000,
                max_input_tokens=6144,
                input_price_per_1k_tokens=0.004,
                output_price_per_1k_tokens=0.008,
            ),
            "Qianfan-Dynamic-8K": QfLLMInfo(
                endpoint="/chat/qianfan-dynamic-8k",
                required_keys={"messages"},
                optional_keys={
                    "stream",
                    "temperature",
                    "top_p",
                    "penalty_score",
                    "system",
                    "user_id",
                    "stop",
                    "max_output_tokens",
                    "response_format",
                    "disable_search",
                    "enable_citation",
                    "enable_trace",
                    "functions",
                    "tool_choice",
                },
                max_input_chars=20000,
                max_input_tokens=5120,
                input_price_per_1k_tokens=0.012,
                output_price_per_1k_tokens=0.012,
            ),
            "ERNIE-Character-8K": QfLLMInfo(
                endpoint="/chat/ernie-char-8k",
                required_keys={"messages"},
                optional_keys={
                    "stream",
                    "temperature",
                    "top_p",
                    "penalty_score",
                    "system",
                    "user_id",
                    "stop",
                    "max_output_tokens",
                },
                max_input_chars=24000,
                max_input_tokens=6144,
                input_price_per_1k_tokens=0.004,
                output_price_per_1k_tokens=0.008,
            ),
            "ERNIE-Character-Fiction-8K": QfLLMInfo(
                endpoint="/chat/ernie-char-fiction-8k",
                required_keys={"messages"},
                optional_keys={
                    "stream",
                    "temperature",
                    "top_p",
                    "penalty_score",
                    "system",
                    "user_id",
                    "stop",
                    "max_output_tokens",
                },
                max_input_chars=24000,
                max_input_tokens=6144,
                input_price_per_1k_tokens=0.004,
                output_price_per_1k_tokens=0.008,
            ),
            "BLOOMZ-7B": QfLLMInfo(
                endpoint="/chat/bloomz_7b1",
                required_keys={"messages"},
                optional_keys={
                    "stream",
                    "user_id",
                    "temperature",
                    "top_k",
                    "top_p",
                    "penalty_score",
                    "stop",
                    "tools",
                    "tool_choice",
                },
                max_input_chars=4800,
                max_input_tokens=None,
                input_price_per_1k_tokens=0.004,
                output_price_per_1k_tokens=0.004,
            ),
            "Llama-2-7B-Chat": QfLLMInfo(
                endpoint="/chat/llama_2_7b",
                required_keys={"messages"},
                optional_keys={
                    "stream",
                    "user_id",
                    "temperature",
                    "top_k",
                    "top_p",
                    "penalty_score",
                    "stop",
                    "tools",
                    "tool_choice",
                },
                max_input_chars=4800,
                max_input_tokens=None,
                input_price_per_1k_tokens=0.004,
                output_price_per_1k_tokens=0.004,
            ),
            "Llama-2-13B-Chat": QfLLMInfo(
                endpoint="/chat/llama_2_13b",
                required_keys={"messages"},
                optional_keys={
                    "stream",
                    "user_id",
                    "temperature",
                    "top_k",
                    "top_p",
                    "penalty_score",
                    "stop",
                    "tools",
                    "tool_choice",
                },
                max_input_chars=4800,
                max_input_tokens=None,
                input_price_per_1k_tokens=0.006,
                output_price_per_1k_tokens=0.006,
            ),
            "Llama-2-70B-Chat": QfLLMInfo(
                endpoint="/chat/llama_2_70b",
                required_keys={"messages"},
                optional_keys={
                    "stream",
                    "user_id",
                    "temperature",
                    "top_k",
                    "top_p",
                    "penalty_score",
                    "stop",
                    "tools",
                    "tool_choice",
                },
                max_input_chars=4800,
                max_input_tokens=None,
                input_price_per_1k_tokens=0.035,
                output_price_per_1k_tokens=0.035,
            ),
            "Meta-Llama-3-8B": QfLLMInfo(
                endpoint="/chat/llama_3_8b",
                required_keys={"messages"},
                optional_keys={
                    "stream",
                    "user_id",
                    "temperature",
                    "top_k",
                    "top_p",
                    "penalty_score",
                    "stop",
                    "tools",
                    "tool_choice",
                },
                max_input_chars=4800,
                max_input_tokens=None,
                input_price_per_1k_tokens=0.004,
                output_price_per_1k_tokens=0.004,
            ),
            "Meta-Llama-3-70B": QfLLMInfo(
                endpoint="/chat/llama_3_70b",
                required_keys={"messages"},
                optional_keys={
                    "stream",
                    "user_id",
                    "temperature",
                    "top_k",
                    "top_p",
                    "penalty_score",
                    "stop",
                    "tools",
                    "tool_choice",
                },
                max_input_chars=4800,
                max_input_tokens=None,
                input_price_per_1k_tokens=0.035,
                output_price_per_1k_tokens=0.035,
            ),
            "Qianfan-BLOOMZ-7B-compressed": QfLLMInfo(
                endpoint="/chat/qianfan_bloomz_7b_compressed",
                required_keys={"messages"},
                optional_keys={
                    "stream",
                    "user_id",
                    "temperature",
                    "top_k",
                    "top_p",
                    "penalty_score",
                    "stop",
                    "tools",
                    "tool_choice",
                },
                max_input_chars=4800,
                max_input_tokens=None,
                input_price_per_1k_tokens=0.004,
                output_price_per_1k_tokens=0.004,
            ),
            "Qianfan-Chinese-Llama-2-7B": QfLLMInfo(
                endpoint="/chat/qianfan_chinese_llama_2_7b",
                required_keys={"messages"},
                optional_keys={
                    "stream",
                    "user_id",
                    "temperature",
                    "top_k",
                    "top_p",
                    "penalty_score",
                    "stop",
                    "tools",
                    "tool_choice",
                },
                max_input_chars=4800,
                max_input_tokens=None,
                input_price_per_1k_tokens=0.004,
                output_price_per_1k_tokens=0.004,
            ),
            "ChatGLM2-6B-32K": QfLLMInfo(
                endpoint="/chat/chatglm2_6b_32k",
                required_keys={"messages"},
                optional_keys={
                    "stream",
                    "user_id",
                    "temperature",
                    "top_k",
                    "top_p",
                    "penalty_score",
                    "stop",
                    "tools",
                    "tool_choice",
                },
                max_input_chars=4800,
                max_input_tokens=None,
                input_price_per_1k_tokens=0.004,
                output_price_per_1k_tokens=0.004,
            ),
            "AquilaChat-7B": QfLLMInfo(
                endpoint="/chat/aquilachat_7b",
                required_keys={"messages"},
                optional_keys={
                    "stream",
                    "user_id",
                    "temperature",
                    "top_k",
                    "top_p",
                    "penalty_score",
                    "stop",
                    "tools",
                    "tool_choice",
                },
                max_input_chars=4800,
                max_input_tokens=None,
                input_price_per_1k_tokens=0.004,
                output_price_per_1k_tokens=0.004,
            ),
            "XuanYuan-70B-Chat-4bit": QfLLMInfo(
                endpoint="/chat/xuanyuan_70b_chat",
                required_keys={"messages"},
                optional_keys={
                    "stream",
                    "user_id",
                    "temperature",
                    "top_k",
                    "top_p",
                    "penalty_score",
                    "stop",
                    "tools",
                    "tool_choice",
                },
                max_input_chars=4800,
                max_input_tokens=None,
                input_price_per_1k_tokens=0.035,
                output_price_per_1k_tokens=0.035,
            ),
            "Qianfan-Chinese-Llama-2-13B": QfLLMInfo(
                endpoint="/chat/qianfan_chinese_llama_2_13b",
                required_keys={"messages"},
                optional_keys={
                    "stream",
                    "user_id",
                    "temperature",
                    "top_k",
                    "top_p",
                    "penalty_score",
                    "stop",
                    "tools",
                    "tool_choice",
                },
                max_input_chars=4800,
                max_input_tokens=None,
                input_price_per_1k_tokens=0.006,
                output_price_per_1k_tokens=0.006,
            ),
            "Qianfan-Chinese-Llama-2-70B": QfLLMInfo(
                endpoint="/chat/qianfan_chinese_llama_2_70b",
                required_keys={"messages"},
                optional_keys={
                    "stream",
                    "user_id",
                    "temperature",
                    "top_k",
                    "top_p",
                    "penalty_score",
                    "stop",
                    "tools",
                    "tool_choice",
                },
                max_input_chars=4800,
                max_input_tokens=None,
                input_price_per_1k_tokens=0.006,
                output_price_per_1k_tokens=0.006,
            ),
            "ChatLaw": QfLLMInfo(
                endpoint="/chat/chatlaw",
                required_keys={"messages", "extra_parameters"},
                optional_keys={
                    "stream",
                    "user_id",
                    "temperature",
                    "top_p",
                    "tools",
                    "tool_choice",
                },
                max_input_chars=4800,
                max_input_tokens=None,
                input_price_per_1k_tokens=0.008,
                output_price_per_1k_tokens=0.008,
            ),
            "Yi-34B-Chat": QfLLMInfo(
                endpoint="/chat/yi_34b_chat",
                required_keys={"messages"},
                optional_keys={
                    "stream",
                    "user_id",
                    "temperature",
                    "top_k",
                    "top_p",
                    "penalty_score",
                    "stop",
                    "tools",
                    "tool_choice",
                },
                max_input_chars=4800,
                max_input_tokens=None,
                # 限时免费
                input_price_per_1k_tokens=0,
                output_price_per_1k_tokens=0,
            ),
            "Mixtral-8x7B-Instruct": QfLLMInfo(
                endpoint="/chat/mixtral_8x7b_instruct",
                required_keys={"messages"},
                optional_keys={
                    "stream",
                    "user_id",
                    "temperature",
                    "top_k",
                    "top_p",
                    "penalty_score",
                    "stop",
                    "tools",
                    "tool_choice",
                },
                max_input_chars=4800,
                max_input_tokens=None,
                input_price_per_1k_tokens=0.035,
                output_price_per_1k_tokens=0.035,
            ),
            "Gemma-7B-it": QfLLMInfo(
                endpoint="/chat/gemma_7b_it",
                required_keys={"messages"},
                optional_keys={
                    "stream",
                    "user_id",
                    "temperature",
                    "top_k",
                    "top_p",
                    "penalty_score",
                    "stop",
                    "tools",
                    "tool_choice",
                },
                max_input_chars=4800,
                max_input_tokens=None,
                input_price_per_1k_tokens=0.004,
                output_price_per_1k_tokens=0.004,
            ),
            UNSPECIFIED_MODEL: QfLLMInfo(
                endpoint="",
                required_keys={"messages"},
                optional_keys=set(),
            ),
        }

        # 处理历史模型名称/别名
        alias = {
            "ERNIE-Speed": "ERNIE-Speed-8K",
            "ERNIE Speed": "ERNIE-Speed-8K",
            "ERNIE 3.5": "ERNIE-3.5-8K",
            "ERNIE-Lite-8K": "ERNIE-Lite-8K-0308",
            "ERNIE-4.0-preview": "ERNIE-4.0-8K-preview",
            "ERNIE-3.5-preview": "ERNIE-3.5-8K-preview",
            "ERNIE-Functions-8K": "ERNIE-Function-8K",
        }
        for src, target in alias.items():
            info_list[src] = info_list[target]

        deprecated_alias = {
            "ERNIE-Bot-4": "ERNIE-4.0-8K",
            "ERNIE-Bot": "ERNIE-3.5-8K",
            "ERNIE-Bot-turbo": "ERNIE-Lite-8K-0922",
            "EB-turbo-AppBuilder": "ERNIE Speed-AppBuilder",
            "ERNIE-Bot-turbo-AI": "ERNIE Speed-AppBuilder",
        }

        for src, target in deprecated_alias.items():
            info = copy.deepcopy(info_list[target])
            info.deprecated = True
            info_list[src] = info
        return info_list

    @classmethod
    def api_type(cls) -> str:
        return "chat"

    @classmethod
    def _default_model(cls) -> str:
        """
        default model of ChatCompletion
        """
        return DefaultLLMModel.ChatCompletion

    def _convert_endpoint(self, model: Optional[str], endpoint: str) -> str:
        """
        convert endpoint to ChatCompletion API endpoint
        """
        return f"/chat/{endpoint}"

    def do(
        self,
        messages: Union[List[Dict], QfMessages],
        model: Optional[str] = None,
        endpoint: Optional[str] = None,
        stream: bool = False,
        retry_count: int = DefaultValue.RetryCount,
        request_timeout: float = DefaultValue.RetryTimeout,
        request_id: Optional[str] = None,
        backoff_factor: float = DefaultValue.RetryBackoffFactor,
        auto_concat_truncate: bool = False,
        truncated_continue_prompt: str = DefaultValue.TruncatedContinuePrompt,
        truncate_overlong_msgs: bool = False,
        **kwargs: Any,
    ) -> Union[QfResponse, Iterator[QfResponse]]:
        """
        Perform chat-based language generation using user-supplied messages.

        Parameters:
          messages (Union[List[Dict], QfMessages]):
            A list of messages in the conversation including the one from system. Each
            message should be a dictionary containing 'role' and 'content' keys,
            representing the role (either 'user', or 'assistant') and content of the
            message, respectively. Alternatively, you can provide a QfMessages object
            for convenience.
          model (Optional[str]):
            The name or identifier of the language model to use. If not specified, the
            default model is used(ERNIE-Lite-8K).
          endpoint (Optional[str]):
            The endpoint for making API requests. If not provided, the default endpoint
            is used.
          stream (bool):
            If set to True, the responses are streamed back as an iterator. If False, a
            single response is returned.
          retry_count (int):
            The number of times to retry the request in case of failure.
          request_timeout (float):
            The maximum time (in seconds) to wait for a response from the model.
          backoff_factor (float):
            A factor to increase the waiting time between retry attempts.
          auto_concat_truncate (bool):
            [Experimental] If set to True, continuously requesting will be run
            until `is_truncated` is `False`. As a result, the entire reply will
            be returned.
            Cause this feature highly relies on the understanding ability of LLM,
            Use it carefully.
          truncated_continue_prompt (str):
            [Experimental] The prompt to use when requesting more content for auto
            truncated reply.
          truncate_overlong_msgs (bool):
            Whether to truncate overlong messages.
          kwargs (Any):
            Additional keyword arguments that can be passed to customize the request.

        Additional parameters like `temperature` will vary depending on the model,
        please refer to the API documentation. The additional parameters can be passed
        as follows:

        ```
        ChatCompletion().do(messages = ..., temperature = 0.2, top_p = 0.5)
        ```

        """
        if isinstance(messages, QfMessages):
            kwargs["messages"] = messages._to_list()
        else:
            kwargs["messages"] = messages

        if request_id is not None:
            kwargs["request_id"] = request_id
        kwargs["_auto_truncate"] = truncate_overlong_msgs

        resp = self._do(
            model,
            stream,
            retry_count,
            request_timeout,
            backoff_factor,
            endpoint=endpoint,
            **kwargs,
        )
        if not auto_concat_truncate:
            return resp
        # continuously request for entire reply
        if stream:
            assert isinstance(resp, Iterator)
            return self._stream_concat_truncated(
                resp,
                kwargs.pop("messages"),
                model,
                endpoint,
                retry_count,
                request_timeout,
                backoff_factor,
                truncated_continue_prompt,
                **kwargs,
            )
        assert isinstance(resp, QfResponse)
        cur_content: str = resp["result"]
        entire_content: str = cur_content
        is_truncated: bool = resp["is_truncated"]
        msgs = copy.deepcopy(messages)
        while is_truncated:
            if isinstance(msgs, QfMessages):
                msgs.append(cur_content, QfRole.Assistant)
                msgs.append(truncated_continue_prompt, QfRole.User)
            else:
                msgs.append({"content": cur_content, "role": "assistant"})
                msgs.append({"content": truncated_continue_prompt, "role": "user"})
            cur_content = ""
            kwargs["messages"] = msgs
            resp = self._do(
                model,
                False,
                retry_count,
                request_timeout,
                backoff_factor,
                endpoint=endpoint,
                **kwargs,
            )
            assert isinstance(resp, QfResponse)
            cur_content += resp["result"]
            entire_content += resp["result"]
            is_truncated = resp["is_truncated"]
            if not is_truncated:
                resp.body["result"] = entire_content
                return resp
        return resp

    def _stream_concat_truncated(
        self,
        first_resp: Iterator[QfResponse],
        messages: Union[List[Dict], QfMessages],
        model: Optional[str] = None,
        endpoint: Optional[str] = None,
        retry_count: int = DefaultValue.RetryCount,
        request_timeout: float = DefaultValue.RetryTimeout,
        backoff_factor: float = DefaultValue.RetryBackoffFactor,
        truncated_continue_prompt: str = DefaultValue.TruncatedContinuePrompt,
        **kwargs: Any,
    ) -> Iterator[QfResponse]:
        """
        Continuously do stream request for all pieces of reply.

        Parameters:
          model (Optional[str]):
            The name or identifier of the language model to use. If not specified, the
            default model is used.
          endpoint (Optional[str]):
            The endpoint for making API requests. If not provided, the default endpoint
            is used.
          stream (bool):
            If set to True, the responses are streamed back as an iterator. If False, a
            single response is returned.
          retry_count (int):
            The number of times to retry the request in case of failure.
          request_timeout (float):
            The maximum time (in seconds) to wait for a response from the model.
          backoff_factor (float):
            A factor to increase the waiting time between retry attempts.
          truncated_continue_prompt (str):
            [Experimental] The prompt to use when requesting more content for auto
            truncated reply.
          kwargs (Any):
            Additional keyword arguments that can be passed to customize the request.

        Yields:
            Iterator[QfResponse]: _description_
        """
        cur_content: str = ""
        for r in first_resp:
            cur_content += r["result"]
            yield r
        is_truncated: bool = True
        while is_truncated:
            if isinstance(messages, QfMessages):
                messages.append(cur_content, QfRole.Assistant)
                messages.append(truncated_continue_prompt, QfRole.User)
            else:
                messages.append({"content": cur_content, "role": "assistant"})
                messages.append({"content": truncated_continue_prompt, "role": "user"})
            cur_content = ""
            kwargs["messages"] = messages
            resp = self._do(
                model,
                True,
                retry_count,
                request_timeout,
                backoff_factor,
                endpoint=endpoint,
                **kwargs,
            )

            for r in resp:
                cur_content += r["result"]
                is_truncated = r["is_truncated"]
                # if r["is_end"] and not is_truncated:
                #     r.body["is_end"] = False
                yield r

    async def ado(
        self,
        messages: Union[List[Dict], QfMessages],
        model: Optional[str] = None,
        endpoint: Optional[str] = None,
        stream: bool = False,
        retry_count: int = DefaultValue.RetryCount,
        request_timeout: float = DefaultValue.RetryTimeout,
        request_id: Optional[str] = None,
        backoff_factor: float = DefaultValue.RetryBackoffFactor,
        auto_concat_truncate: bool = False,
        truncated_continue_prompt: str = DefaultValue.TruncatedContinuePrompt,
        truncate_overlong_msgs: bool = False,
        **kwargs: Any,
    ) -> Union[QfResponse, AsyncIterator[QfResponse]]:
        """
        Async perform chat-based language generation using user-supplied messages.

        Parameters:
          messages (Union[List[Dict], QfMessages]):
            A list of messages in the conversation including the one from system. Each
            message should be a dictionary containing 'role' and 'content' keys,
            representing the role (either 'user', or 'assistant') and content of the
            message, respectively. Alternatively, you can provide a QfMessages object
            for convenience.
          model (Optional[str]):
            The name or identifier of the language model to use. If not specified, the
            default model is used(ERNIE-Lite-8K).
          endpoint (Optional[str]):
            The endpoint for making API requests. If not provided, the default endpoint
            is used.
          stream (bool):
            If set to True, the responses are streamed back as an iterator. If False,
            a single response is returned.
          retry_count (int):
            The number of times to retry the request in case of failure.
          request_timeout (float):
            The maximum time (in seconds) to wait for a response from the model.
          backoff_factor (float):
            A factor to increase the waiting time between retry attempts.
          auto_concat_truncate (bool):
            [Experimental] If set to True, continuously requesting will be run
            until `is_truncated` is `False`. As a result, the entire reply will
            be returned.
            Cause this feature highly relies on the understanding ability of LLM,
            Use it carefully.
          truncated_continue_prompt (str):
            [Experimental] The prompt to use when requesting more content for auto
            truncated reply.
          truncate_overlong_msgs (bool):
            Whether to truncate overlong messages.
          kwargs (Any):
            Additional keyword arguments that can be passed to customize the request.

        Additional parameters like `temperature` will vary depending on the model,
        please refer to the API documentation. The additional parameters can be passed
        as follows:

        ```
        ChatCompletion().ado(messages = ..., temperature = 0.2, top_p = 0.5)
        ```

        """
        if isinstance(messages, QfMessages):
            kwargs["messages"] = messages._to_list()
        else:
            kwargs["messages"] = messages

        if request_id is not None:
            kwargs["request_id"] = request_id
        kwargs["_auto_truncate"] = truncate_overlong_msgs

        resp = await self._ado(
            model,
            stream,
            retry_count,
            request_timeout,
            backoff_factor,
            endpoint=endpoint,
            **kwargs,
        )
        if not auto_concat_truncate:
            return resp
        if stream:
            assert isinstance(resp, AsyncIterator)
            return self._async_stream_concat_truncated(
                resp,
                kwargs.pop("messages"),
                model,
                endpoint,
                retry_count,
                request_timeout,
                backoff_factor,
                **kwargs,
            )

        assert isinstance(resp, QfResponse)
        cur_content: str = resp["result"]
        entire_content: str = cur_content
        is_truncated: bool = resp["is_truncated"]

        msgs = copy.deepcopy(messages)
        while is_truncated:
            if isinstance(msgs, QfMessages):
                msgs.append(cur_content, QfRole.Assistant)
                msgs.append(truncated_continue_prompt, QfRole.User)
            else:
                msgs.append({"content": cur_content, "role": "assistant"})
                msgs.append({"content": truncated_continue_prompt, "role": "user"})
            cur_content = ""
            kwargs["messages"] = msgs
            resp = await self._ado(
                model,
                stream,
                retry_count,
                request_timeout,
                backoff_factor,
                endpoint=endpoint,
                **kwargs,
            )
            assert isinstance(resp, QfResponse)
            cur_content += resp["result"]
            entire_content += resp["result"]
            is_truncated = resp["is_truncated"]
            if not is_truncated:
                resp.body["result"] = entire_content
                return resp
        return resp

    async def _async_stream_concat_truncated(
        self,
        first_resp: AsyncIterator[QfResponse],
        messages: Union[List[Dict], QfMessages],
        model: Optional[str] = None,
        endpoint: Optional[str] = None,
        retry_count: int = DefaultValue.RetryCount,
        request_timeout: float = DefaultValue.RetryTimeout,
        backoff_factor: float = DefaultValue.RetryBackoffFactor,
        truncated_continue_prompt: str = DefaultValue.TruncatedContinuePrompt,
        **kwargs: Any,
    ) -> AsyncIterator[QfResponse]:
        """
        Stream concat.
        """
        cur_content: str = ""
        async for r in first_resp:
            cur_content += r["result"]
            yield r
        is_truncated: bool = True
        while is_truncated:
            if isinstance(messages, QfMessages):
                messages.append(cur_content, QfRole.Assistant)
                messages.append(truncated_continue_prompt, QfRole.User)
            else:
                messages.append({"content": cur_content, "role": "assistant"})
                messages.append({"content": truncated_continue_prompt, "role": "user"})
            cur_content = ""
            kwargs["messages"] = messages

            resp = await self._ado(
                model,
                True,
                retry_count,
                request_timeout,
                backoff_factor,
                endpoint=endpoint,
                **kwargs,
            )
            assert isinstance(resp, AsyncIterator)
            async for r in resp:
                cur_content += r["result"]
                is_truncated = r["is_truncated"]
                yield r

    def _generate_body(
        self, model: Optional[str], stream: bool, **kwargs: Any
    ) -> JsonBody:
        """
        generate body
        """
        truncate_msg = kwargs["_auto_truncate"]
        del kwargs["_auto_truncate"]

        body = super()._generate_body(model, stream, **kwargs)
        if not truncate_msg or len(body["messages"]) <= 1:
            return body

        # truncate the messages if the length is too long
        model_info: Optional[QfLLMInfo] = None
        if model is not None:
            try:
                model_info = self.get_model_info(model)
            except errors.InvalidArgumentError:
                ...
        endpoint = self._extract_endpoint(**kwargs)
        if model_info is None:
            # 使用默认模型
            try:
                default_model_info = self.get_model_info(self._default_model())
                if default_model_info.endpoint == endpoint:
                    model_info = default_model_info
            except errors.InvalidArgumentError:
                ...

        # 非默认模型
        if model_info is None:
            model_info = self._self_supported_models()[UNSPECIFIED_MODEL]

        if model_info.max_input_chars is not None:
            chars_limit = model_info.max_input_chars
            if "system" in body:
                chars_limit -= len(body["system"])
            msg_list = body["messages"]
            last_msg = msg_list[-1]
            cur_length = len(last_msg["content"]) if last_msg.get("content") else 0
            new_messages = [last_msg]
            for m in reversed(body["messages"][:-1]):
                cur_length += len(m["content"]) if m.get("content") else 0
                if cur_length > chars_limit:
                    break
                new_messages = [m] + new_messages
            if len(new_messages) % 2 != 1:
                new_messages = new_messages[1:]
            if len(body["messages"]) != len(new_messages):
                log_info(
                    "Top {} messages are truncated due to max_input_chars limit".format(
                        len(body["messages"]) - len(new_messages)
                    )
                )
            body["messages"] = new_messages

        if model_info.max_input_tokens is not None:
            token_limit = model_info.max_input_tokens
            if "system" in body:
                token_limit -= Tokenizer.count_tokens(body["system"], mode="local")
            msg_list = body["messages"]
            last_msg = msg_list[-1]
            cur_length = (
                Tokenizer.count_tokens(last_msg["content"], mode="local")
                if last_msg.get("content")
                else 0
            )
            new_messages = [last_msg]
            for m in reversed(body["messages"][:-1]):
                cur_length += (
                    Tokenizer.count_tokens(m["content"], mode="local")
                    if m.get("content")
                    else 0
                )
                if cur_length > token_limit:
                    break
                new_messages = [m] + new_messages
            if len(new_messages) % 2 != 1:
                new_messages = new_messages[1:]
            if len(body["messages"]) != len(new_messages):
                log_info(
                    "Top {} messages are truncated due to max_input_tokens limit"
                    .format(len(body["messages"]) - len(new_messages))
                )
            body["messages"] = new_messages

        return body


class _ChatCompletionV2(BaseResourceV2):
    @classmethod
    def api_type(cls) -> str:
        return "chat"

    def _api_path(self) -> str:
        return self.config.CHAT_V2_API_ROUTE

    def do(
        self,
        messages: Union[List[Dict], QfMessages],
        model: Optional[str] = None,
        endpoint: Optional[str] = None,
        stream: bool = False,
        retry_count: int = DefaultValue.RetryCount,
        request_timeout: float = DefaultValue.RetryTimeout,
        request_id: Optional[str] = None,
        backoff_factor: float = DefaultValue.RetryBackoffFactor,
        auto_concat_truncate: bool = False,
        truncated_continue_prompt: str = DefaultValue.TruncatedContinuePrompt,
        truncate_overlong_msgs: bool = False,
        **kwargs: Any,
    ) -> Union[QfResponse, Iterator[QfResponse]]:
        if isinstance(messages, QfMessages):
            messages = messages._to_list()
        return self._do(
            messages=messages,
            model=model,
            stream=stream,
            retry_count=retry_count,
            request_timeout=request_timeout,
            request_id=request_id,
            backoff_factor=backoff_factor,
            **kwargs,
        )

    async def ado(
        self,
        messages: Union[List[Dict], QfMessages],
        model: Optional[str] = None,
        endpoint: Optional[str] = None,
        stream: bool = False,
        retry_count: int = DefaultValue.RetryCount,
        request_timeout: float = DefaultValue.RetryTimeout,
        request_id: Optional[str] = None,
        backoff_factor: float = DefaultValue.RetryBackoffFactor,
        auto_concat_truncate: bool = False,
        truncated_continue_prompt: str = DefaultValue.TruncatedContinuePrompt,
        truncate_overlong_msgs: bool = False,
        **kwargs: Any,
    ) -> Union[QfResponse, AsyncIterator[QfResponse]]:
        if isinstance(messages, QfMessages):
            messages = messages._to_list()
        return await self._ado(
            messages=messages,
            model=model,
            stream=stream,
            retry_count=retry_count,
            request_timeout=request_timeout,
            request_id=request_id,
            backoff_factor=backoff_factor,
            **kwargs,
        )

    @classmethod
    def _default_model(cls) -> str:
        return DefaultLLMModel.ChatCompletionV2


class ChatCompletion(VersionBase):
    _real: Union[_ChatCompletionV1, _ChatCompletionV2]

    @classmethod
    def _real_base(cls, version: str, **kwargs: Any) -> Type:
        if version == "1":
            # convert to qianfan.Function, only for api v1
            if kwargs.get("use_function"):
                return Function
            else:
                model = kwargs.get("model") or ""
                func_model_info_list = {
                    k.lower(): v
                    for k, v in Function(**kwargs)._self_supported_models().items()
                }
                func_model_info = func_model_info_list.get(model.lower())
                if model and func_model_info:
                    if func_model_info and func_model_info.endpoint:
                        return Function
                endpoint = kwargs.get("endpoint", "")
                if endpoint:
                    for m in func_model_info_list.values():
                        if endpoint and m.endpoint == endpoint:
                            return Function
            return _ChatCompletionV1
        elif version == "2":
            if kwargs.get("use_function") or kwargs.get("model") == "ernie-func-8k":
                return FunctionV2
            return _ChatCompletionV2
        raise errors.InvalidArgumentError("Invalid version")

    def do(
        self,
        messages: Union[List[Dict], QfMessages],
        model: Optional[str] = None,
        endpoint: Optional[str] = None,
        stream: bool = False,
        retry_count: int = DefaultValue.RetryCount,
        request_timeout: float = DefaultValue.RetryTimeout,
        request_id: Optional[str] = None,
        backoff_factor: float = DefaultValue.RetryBackoffFactor,
        auto_concat_truncate: bool = False,
        truncated_continue_prompt: str = DefaultValue.TruncatedContinuePrompt,
        truncate_overlong_msgs: bool = False,
        adapt_openai_message_format: bool = False,
        **kwargs: Any,
    ) -> Union[QfResponse, Iterator[QfResponse]]:
        """
        Perform chat-based language generation using user-supplied messages.

        Parameters:
          messages (Union[List[Dict], QfMessages]):
            A list of messages in the conversation including the one from system. Each
            message should be a dictionary containing 'role' and 'content' keys,
            representing the role (either 'user', or 'assistant') and content of the
            message, respectively. Alternatively, you can provide a QfMessages object
            for convenience.
          model (Optional[str]):
            The name or identifier of the language model to use. If not specified, the
            default model is used(ERNIE-Lite-8K).
          endpoint (Optional[str]):
            The endpoint for making API requests. If not provided, the default endpoint
            is used.
          stream (bool):
            If set to True, the responses are streamed back as an iterator. If False, a
            single response is returned.
          retry_count (int):
            The number of times to retry the request in case of failure.
          request_timeout (float):
            The maximum time (in seconds) to wait for a response from the model.
          backoff_factor (float):
            A factor to increase the waiting time between retry attempts.
          auto_concat_truncate (bool):
            [Experimental] If set to True, continuously requesting will be run
            until `is_truncated` is `False`. As a result, the entire reply will
            be returned.
            Cause this feature highly relies on the understanding ability of LLM,
            Use it carefully.
          truncated_continue_prompt (str):
            [Experimental] The prompt to use when requesting more content for auto
            truncated reply.
          truncate_overlong_msgs (bool):
            Whether to truncate overlong messages.
          adapt_openai_message_format (bool):
            whether to adapt openai message format, such as `system` default is False.
          kwargs (Any):
            Additional keyword arguments that can be passed to customize the request.

        Additional parameters like `temperature` will vary depending on the model,
        please refer to the API documentation. The additional parameters can be passed
        as follows:

        ```
        ChatCompletion(version=2).do(messages = ..., temperature = 0.2, top_p = 0.5)
        ```
        """
        if adapt_openai_message_format:
            # todo more message format
            system, messages = self._adapt_messages_format(messages)
            if "system" not in kwargs and system:
                kwargs["system"] = system
        if model is not None or endpoint is not None:
            # TODO兼容 v2调用ernie-func-8k
            real_base_type = self._real_base(
                self._version, model=model, endpoint=endpoint, **kwargs
            )
            if real_base_type is Function:
                # 不影响ChatCompletion流程，兼容Function调用
                tmpImpl = real_base_type(**kwargs)
                return tmpImpl.do(
                    messages=messages,
                    endpoint=endpoint,
                    model=model,
                    stream=stream,
                    retry_count=retry_count,
                    request_timeout=request_timeout,
                    request_id=request_id,
                    backoff_factor=backoff_factor,
                    auto_concat_truncate=auto_concat_truncate,
                    truncated_continue_prompt=truncated_continue_prompt,
                    truncate_overlong_msgs=truncate_overlong_msgs,
                    **kwargs,
                )
        return self._do(
            messages=messages,
            endpoint=endpoint,
            model=model,
            stream=stream,
            retry_count=retry_count,
            request_timeout=request_timeout,
            request_id=request_id,
            backoff_factor=backoff_factor,
            auto_concat_truncate=auto_concat_truncate,
            truncated_continue_prompt=truncated_continue_prompt,
            truncate_overlong_msgs=truncate_overlong_msgs,
            **kwargs,
        )

    async def ado(
        self,
        messages: Union[List[Dict], QfMessages],
        model: Optional[str] = None,
        endpoint: Optional[str] = None,
        stream: bool = False,
        retry_count: int = DefaultValue.RetryCount,
        request_timeout: float = DefaultValue.RetryTimeout,
        request_id: Optional[str] = None,
        backoff_factor: float = DefaultValue.RetryBackoffFactor,
        auto_concat_truncate: bool = False,
        truncated_continue_prompt: str = DefaultValue.TruncatedContinuePrompt,
        truncate_overlong_msgs: bool = False,
        adapt_openai_message_format: bool = False,
        **kwargs: Any,
    ) -> Union[QfResponse, AsyncIterator[QfResponse]]:
        """
        Async perform chat-based language generation using user-supplied messages.

        Parameters:
          messages (Union[List[Dict], QfMessages]):
            A list of messages in the conversation including the one from system. Each
            message should be a dictionary containing 'role' and 'content' keys,
            representing the role (either 'user', or 'assistant') and content of the
            message, respectively. Alternatively, you can provide a QfMessages object
            for convenience.
          model (Optional[str]):
            The name or identifier of the language model to use. If not specified, the
            default model is used(ERNIE-Lite-8K).
          endpoint (Optional[str]):
            The endpoint for making API requests. If not provided, the default endpoint
            is used.
          stream (bool):
            If set to True, the responses are streamed back as an iterator. If False,
            a single response is returned.
          retry_count (int):
            The number of times to retry the request in case of failure.
          request_timeout (float):
            The maximum time (in seconds) to wait for a response from the model.
          backoff_factor (float):
            A factor to increase the waiting time between retry attempts.
          auto_concat_truncate (bool):
            [Experimental] If set to True, continuously requesting will be run
            until `is_truncated` is `False`. As a result, the entire reply will
            be returned.
            Cause this feature highly relies on the understanding ability of LLM,
            Use it carefully.
          truncated_continue_prompt (str):
            [Experimental] The prompt to use when requesting more content for auto
            truncated reply.
          truncate_overlong_msgs (bool):
            Whether to truncate overlong messages.
          adapt_openai_message_format (bool):
            whether to adapt openai message format, such as `system` default is False.
          kwargs (Any):
            Additional keyword arguments that can be passed to customize the request.

        Additional parameters like `temperature` will vary depending on the model,
        please refer to the API documentation. The additional parameters can be passed
        as follows:

        ```
        ChatCompletion().ado(messages = ..., temperature = 0.2, top_p = 0.5)
        ```

        """
        if adapt_openai_message_format:
            system, messages = self._adapt_messages_format(messages)
            if "system" not in kwargs and system:
                kwargs["system"] = system
        if model is not None or endpoint is not None:
            # TODO兼容 v2调用ernie-func-8k
            real_base_type = self._real_base(
                self._version, model=model, endpoint=endpoint, **kwargs
            )
            if real_base_type is Function:
                # 不影响ChatCompletion流程，兼容Function调用
                tmpImpl = real_base_type(**kwargs)
                return await tmpImpl.ado(
                    messages=messages,
                    endpoint=endpoint,
                    model=model,
                    stream=stream,
                    retry_count=retry_count,
                    request_timeout=request_timeout,
                    request_id=request_id,
                    backoff_factor=backoff_factor,
                    auto_concat_truncate=auto_concat_truncate,
                    truncated_continue_prompt=truncated_continue_prompt,
                    truncate_overlong_msgs=truncate_overlong_msgs,
                    **kwargs,
                )
        return await self._ado(
            messages=messages,
            model=model,
            endpoint=endpoint,
            stream=stream,
            retry_count=retry_count,
            request_timeout=request_timeout,
            request_id=request_id,
            backoff_factor=backoff_factor,
            auto_concat_truncate=auto_concat_truncate,
            truncated_continue_prompt=truncated_continue_prompt,
            truncate_overlong_msgs=truncate_overlong_msgs,
            **kwargs,
        )

    def _adapt_messages_format(
        self, messages: Optional[Union[List[Dict], QfMessages]] = None
    ) -> Tuple[str, List[Dict]]:
        if messages is None:
            return "", []
        if isinstance(messages, QfMessages):
            messages = messages._to_list()
        system = ""
        filtered_messages = []
        for message in messages:
            if message.get("role") == "system":
                system += message.get("content", "")
            else:
                filtered_messages.append(message)  # 保留非 system 的 message
        return system, filtered_messages

    def batch_do(
        self,
        messages_list: Optional[Union[List[List[Dict]], List[QfMessages]]] = None,
        body_list: Optional[List[Dict]] = None,
        show_total_latency: bool = False,
        worker_num: Optional[int] = None,
        **kwargs: Any,
    ) -> BatchRequestFuture:
        """
        Batch perform chat-based language generation using user-supplied messages.

        Parameters:
          messages_list: (Optional[List[Union[List[Dict], QfMessages]]]):
            List of the messages list in the conversation. Please refer to
            `ChatCompletion.do` for more information of each messages.
            Make sure you only take either `messages_list` or `body_list` as
            your argument. Default to None.
          body_list: (Optional[List[Dict]]):
            List of body for `ChatCompletion.do`.
            Make sure you only take either `messages_list` or `body_list` as
            your argument. Default to None.
          show_total_latency: (bool):
            Whether auto reading all results in worker function, without any waiting
            in streaming request situation. Default to False.
          worker_num (Optional[int]):
            The number of prompts to process at the same time, default to None,
            which means this number will be decided dynamically.
          kwargs (Any):
            Please refer to `ChatCompletion.do` for other parameters such as
            `model`, `endpoint`, `retry_count`, etc.

        ```
        response_list = ChatCompletion().batch_do([...], worker_num = 10)
        for response in response_list:
            # return QfResponse if succeed, or exception will be raised
            print(response.result())
        # or
        while response_list.finished_count() != response_list.task_count():
            time.sleep(1)
        print(response_list.results())
        ```

        """

        if "enable_reading_buffer" in kwargs:
            log_warn(
                "enable_reading_buffer has been deprecated, please use"
                " show_total_latency instead"
            )
            if (
                isinstance(kwargs["enable_reading_buffer"], bool)
                and kwargs["enable_reading_buffer"]
            ):
                show_total_latency = True

        def worker(
            inner_func: Callable, **kwargs: Any
        ) -> Union[List[QfResponse], Iterator[QfResponse], QfResponse, Exception]:
            return inner_func(**kwargs, show_total_latency=show_total_latency)

        task_list: List[Callable]

        if messages_list:
            task_list = [
                partial(worker, self.do, messages=messages, **kwargs)
                for index, messages in enumerate(messages_list)
            ]
        elif body_list:
            task_list = []
            for index, body in enumerate(body_list):
                new_kwargs = {**kwargs}
                new_kwargs.update(body)
                task_list.append(partial(worker, self.do, **new_kwargs))
        else:
            err_msg = (
                "Make sure you set either `messages_list` or `body_list` as your"
                " argument."
            )
            log_error(err_msg)
            raise ValueError(err_msg)

        return self._real._batch_request(task_list, worker_num)

    async def abatch_do(
        self,
        messages_list: Optional[Union[List[List[Dict]], List[QfMessages]]] = None,
        body_list: Optional[List[Dict]] = None,
        show_total_latency: bool = False,
        worker_num: Optional[int] = None,
        **kwargs: Any,
    ) -> List[Union[QfResponse, AsyncIterator[QfResponse]]]:
        """
        Async batch perform chat-based language generation using user-supplied messages.

        Parameters:
          messages_list: (Optional[List[Union[List[Dict], QfMessages]]]):
            List of the messages list in the conversation. Please refer to
            `ChatCompletion.do` for more information of each messages.
            Make sure you only take either `messages_list` or `body_list` as
            your argument. Default to None.
          body_list: (Optional[List[Dict]]):
            List of body for `ChatCompletion.do`.
            Make sure you only take either `messages_list` or `body_list` as
            your argument. Default to None.
          show_total_latency: (bool):
            Whether auto reading all results in worker function, without any waiting
            in streaming request situation. Default to False.
          worker_num (Optional[int]):
            The number of prompts to process at the same time, default to None,
            which means this number will be decided dynamically.
          kwargs (Any):
            Please refer to `ChatCompletion.do` for other parameters such as
            `model`, `endpoint`, `retry_count`, etc.

        ```
        response_list = await ChatCompletion().abatch_do([...], worker_num = 10)
        for response in response_list:
            # response is `QfResponse` if succeed, or response will be exception
            print(response)
        ```

        """

        if "enable_reading_buffer" in kwargs:
            log_warn(
                "enable_reading_buffer has been deprecated, please use"
                " show_total_latency instead"
            )
            if (
                isinstance(kwargs["enable_reading_buffer"], bool)
                and kwargs["enable_reading_buffer"]
            ):
                show_total_latency = True

        task_list: List[Callable]

        async def worker(
            inner_func: Callable, **kwargs: Any
        ) -> Union[List[QfResponse], Iterator[QfResponse], QfResponse, Exception]:
            return await inner_func(**kwargs, show_total_latency=show_total_latency)

        if messages_list:
            task_list = [
                partial(worker, self.ado, messages=messages, **kwargs)
                for messages in messages_list
            ]
        elif body_list:
            task_list = []
            for body in body_list:
                new_kwargs = {**kwargs}
                new_kwargs.update(body)
                task_list.append(partial(worker, self.ado, **new_kwargs))
        else:
            err_msg = (
                "Make sure you set either `messages_list` or `body_list` as your"
                " argument."
            )
            log_error(err_msg)
            raise ValueError(err_msg)

        tasks = [task() for task in task_list]
        return await self._real._abatch_request(tasks, worker_num)

    def create(
        self,
        messages: Union[List[Dict], QfMessages],
        model: Optional[str] = None,
        endpoint: Optional[str] = None,
        stream: bool = False,
        retry_count: int = DefaultValue.RetryCount,
        request_timeout: float = DefaultValue.RetryTimeout,
        request_id: Optional[str] = None,
        backoff_factor: float = DefaultValue.RetryBackoffFactor,
        auto_concat_truncate: bool = False,
        truncated_continue_prompt: str = DefaultValue.TruncatedContinuePrompt,
        truncate_overlong_msgs: bool = False,
        **kwargs: Any,
    ) -> Union[Completion, Iterator[CompletionChunk], QfResponse, Iterator[QfResponse]]:
        if self._version == "1":
            return self.do(
                messages=messages,
                endpoint=endpoint,
                model=model,
                stream=stream,
                retry_count=retry_count,
                request_timeout=request_timeout,
                request_id=request_id,
                backoff_factor=backoff_factor,
                auto_concat_truncate=auto_concat_truncate,
                truncated_continue_prompt=truncated_continue_prompt,
                truncate_overlong_msgs=truncate_overlong_msgs,
                **kwargs,
            )
        resp = self.do(
            messages=messages,
            endpoint=endpoint,
            model=model,
            stream=stream,
            retry_count=retry_count,
            request_timeout=request_timeout,
            request_id=request_id,
            backoff_factor=backoff_factor,
            auto_concat_truncate=auto_concat_truncate,
            truncated_continue_prompt=truncated_continue_prompt,
            truncate_overlong_msgs=truncate_overlong_msgs,
            **kwargs,
        )
        if not stream:
            assert isinstance(resp, QfResponse)
            return Completion.parse_obj(resp.body)
        else:
            assert isinstance(resp, Iterator)
            return self._create_completion_stream(resp)

    async def acreate(
        self,
        messages: Union[List[Dict], QfMessages],
        model: Optional[str] = None,
        endpoint: Optional[str] = None,
        stream: bool = False,
        retry_count: int = DefaultValue.RetryCount,
        request_timeout: float = DefaultValue.RetryTimeout,
        request_id: Optional[str] = None,
        backoff_factor: float = DefaultValue.RetryBackoffFactor,
        auto_concat_truncate: bool = False,
        truncated_continue_prompt: str = DefaultValue.TruncatedContinuePrompt,
        truncate_overlong_msgs: bool = False,
        **kwargs: Any,
    ) -> Union[
        Completion,
        AsyncIterator[CompletionChunk],
        QfResponse,
        AsyncIterator[QfResponse],
    ]:
        if self._version == "1":
            return await self.ado(
                messages=messages,
                endpoint=endpoint,
                model=model,
                stream=stream,
                retry_count=retry_count,
                request_timeout=request_timeout,
                request_id=request_id,
                backoff_factor=backoff_factor,
                auto_concat_truncate=auto_concat_truncate,
                truncated_continue_prompt=truncated_continue_prompt,
                truncate_overlong_msgs=truncate_overlong_msgs,
                **kwargs,
            )
        resp = await self.ado(
            messages=messages,
            endpoint=endpoint,
            model=model,
            stream=stream,
            retry_count=retry_count,
            request_timeout=request_timeout,
            request_id=request_id,
            backoff_factor=backoff_factor,
            auto_concat_truncate=auto_concat_truncate,
            truncated_continue_prompt=truncated_continue_prompt,
            truncate_overlong_msgs=truncate_overlong_msgs,
            **kwargs,
        )
        if not stream:
            assert isinstance(resp, QfResponse)
            return Completion.parse_obj(resp.body)
        else:
            assert isinstance(resp, AsyncIterator)
            return self._acreate_completion_stream(resp)

    def _create_completion_stream(
        self, resp: Iterator[QfResponse]
    ) -> Iterator[CompletionChunk]:
        for r in resp:
            yield CompletionChunk.parse_obj(r.body)

    async def _acreate_completion_stream(
        self, resp: AsyncIterator[QfResponse]
    ) -> AsyncIterator[CompletionChunk]:
        async for r in resp:
            yield CompletionChunk.parse_obj(r.body)

    def _convert_v2_request_to_v1(self, request: Any) -> Any:
        # TODO: V2 model to V1 model
        return request

    def _convert_v2_response_to_v1(self, response: QfResponse) -> QfResponse:
        response.body["choices"] = [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": response["result"],
                },
                "need_clear_history": response["need_clear_history"],
            }
        ]
        return response

    def _convert_v2_response_to_v1_stream(
        self, iterator: Iterator[QfResponse]
    ) -> Iterator[QfResponse]:
        for i in iterator:
            i.body["choices"] = [{"index": 0, "delta": {"content": i["result"]}}]
            yield i

    async def _convert_v2_response_to_v1_async_stream(
        self, iterator: AsyncIterator[QfResponse]
    ) -> AsyncIterator[QfResponse]:
        async for i in iterator:
            i.body["choices"] = [{"index": 0, "delta": {"content": i["result"]}}]
            yield i
