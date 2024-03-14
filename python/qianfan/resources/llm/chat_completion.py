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
from typing import Any, AsyncIterator, Dict, Iterator, List, Optional, Union

from qianfan.config import get_config
from qianfan.consts import DefaultLLMModel, DefaultValue
from qianfan.resources.llm.base import (
    UNSPECIFIED_MODEL,
    BaseResource,
    BatchRequestFuture,
)
from qianfan.resources.tools.tokenizer import Tokenizer
from qianfan.resources.typing import JsonBody, QfLLMInfo, QfMessages, QfResponse, QfRole
from qianfan.utils.logging import log_info


class ChatCompletion(BaseResource):
    """
    QianFan ChatCompletion is an agent for calling QianFan ChatCompletion API.
    """

    @classmethod
    def _supported_models(cls) -> Dict[str, QfLLMInfo]:
        """
        preset model services list of ChatCompletion

        Args:
            None

        Returns:
            a dict which key is preset model and value is the endpoint

        """
        info_list = {
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
                },
                max_input_chars=11200,
                max_input_tokens=7168,
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
                },
                max_input_chars=11200,
                max_input_tokens=7168,
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
                },
                max_input_chars=20000,
                max_input_tokens=5120,
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
                },
                max_input_chars=20000,
                max_input_tokens=5120,
            ),
            "ERNIE-Bot-8k": QfLLMInfo(
                endpoint="/chat/ernie_bot_8k",
                required_keys={"messages"},
                optional_keys={
                    "functions",
                    "temperature",
                    "top_p",
                    "penalty_score",
                    "stream",
                    "system",
                    "stop",
                    "disable_search",
                    "enable_citation",
                    "user_id",
                    "response_format",
                    "max_output_tokens",
                },
                max_input_chars=20000,
                max_input_tokens=5120,
            ),
            "ERNIE-3.5-4K-0205": QfLLMInfo(
                endpoint="/chat/ernie-3.5-4k-0205",
                required_keys={"messages"},
                optional_keys={
                    "functions",
                    "temperature",
                    "top_p",
                    "penalty_score",
                    "stream",
                    "system",
                    "stop",
                    "disable_search",
                    "enable_citation",
                    "user_id",
                    "response_format",
                    "max_output_tokens",
                },
                max_input_chars=8000,
                max_input_tokens=2048,
            ),
            "ERNIE-3.5-8K-0205": QfLLMInfo(
                endpoint="/chat/ernie-3.5-8k-0205",
                required_keys={"messages"},
                optional_keys={
                    "functions",
                    "temperature",
                    "top_p",
                    "penalty_score",
                    "stream",
                    "system",
                    "stop",
                    "disable_search",
                    "enable_citation",
                    "user_id",
                    "response_format",
                    "max_output_tokens",
                },
                max_input_chars=20000,
                max_input_tokens=5120,
            ),
            "ERNIE-3.5-8K-1222": QfLLMInfo(
                endpoint="/chat/ernie-3.5-8k-1222",
                required_keys={"messages"},
                optional_keys={
                    "functions",
                    "temperature",
                    "top_p",
                    "penalty_score",
                    "stream",
                    "system",
                    "stop",
                    "disable_search",
                    "enable_citation",
                    "user_id",
                    "response_format",
                    "max_output_tokens",
                },
                max_input_chars=20000,
                max_input_tokens=5120,
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
                },
                max_input_chars=11200,
                max_input_tokens=7168,
            ),
            "ERNIE-Speed-128k": QfLLMInfo(
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
                },
                max_input_chars=507904,
                max_input_tokens=126976,
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
            ),
            "Llama-2-7b-chat": QfLLMInfo(
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
            ),
            "Llama-2-13b-chat": QfLLMInfo(
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
            ),
            "Llama-2-70b-chat": QfLLMInfo(
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
            ),
            UNSPECIFIED_MODEL: QfLLMInfo(
                endpoint="",
                required_keys={"messages"},
                optional_keys=set(),
            ),
        }
        alias = {
            "ERNIE-Speed": "ERNIE-Speed-8K",
            "ERNIE Speed": "ERNIE-Speed-8K",
            "ERNIE 3.5": "ERNIE-3.5-8K",
        }
        for src, target in alias.items():
            info_list[src] = info_list[target]

        depracated_alias = {
            "ERNIE-Bot-4": "ERNIE-4.0-8K",
            "ERNIE-Bot": "ERNIE-3.5-8K",
            "ERNIE-Bot-turbo": "ERNIE-Lite-8K-0922",
            "EB-turbo-AppBuilder": "ERNIE Speed-AppBuilder",
            "ERNIE-Bot-turbo-AI": "ERNIE Speed-AppBuilder",
        }
        for src, target in depracated_alias.items():
            info = copy.deepcopy(info_list[target])
            info.depracated = True
            info_list[src] = info
        return info_list

    @classmethod
    def _default_model(cls) -> str:
        """
        default model of ChatCompletion `ERNIE-Bot-turbo`

        Args:
            None

        Returns:
           "ERNIE-Bot-turbo"

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
            default model is used(ERNIE-Bot-turbo).
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
        if (
            not get_config().DISABLE_EB_SDK
            and get_config().EB_SDK_INSTALLED
            and model in ["ERNIE-Bot-turbo", "ERNIE-Bot"]
        ):
            import erniebot

            erniebot.ak = self._client._auth._ak
            erniebot.sk = self._client._auth._sk
            erniebot.access_token = self._client._auth.access_token()
            # compat with eb sdk
            if model == "ERNIE-Bot":
                model = "ernie-bot-3.5"
            return erniebot.ChatCompletion.create(  # type: ignore
                model=model.lower(), stream=stream, **kwargs
            )
        if request_id is not None:
            kwargs["request_id"] = request_id
        kwargs["_auto_truncate"] = truncate_overlong_msgs

        resp = self._do(
            model,
            endpoint,
            stream,
            retry_count,
            request_timeout,
            backoff_factor,
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
                endpoint,
                False,
                retry_count,
                request_timeout,
                backoff_factor,
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
            default model is used(ERNIE-Bot-turbo).
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
                endpoint,
                True,
                retry_count,
                request_timeout,
                backoff_factor,
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
            default model is used(ERNIE-Bot-turbo).
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
        if (
            not get_config().DISABLE_EB_SDK
            and get_config().EB_SDK_INSTALLED
            and model in ["ERNIE-Bot-turbo", "ERNIE-Bot"]
        ):
            import erniebot

            erniebot.ak = self._client._auth._ak
            erniebot.sk = self._client._auth._sk
            erniebot.access_token = self._client._auth.access_token()
            # compat with eb sdk
            if model == "ERNIE-Bot":
                model = "ernie-bot-3.5"
            return await erniebot.ChatCompletion.acreate(  # type: ignore
                model=model.lower(), stream=stream, **kwargs
            )
        if request_id is not None:
            kwargs["request_id"] = request_id
        kwargs["_auto_truncate"] = truncate_overlong_msgs

        resp = await self._ado(
            model,
            endpoint,
            stream,
            retry_count,
            request_timeout,
            backoff_factor,
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
                endpoint,
                stream,
                retry_count,
                request_timeout,
                backoff_factor,
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
                endpoint,
                True,
                retry_count,
                request_timeout,
                backoff_factor,
                **kwargs,
            )
            assert isinstance(resp, AsyncIterator)
            async for r in resp:
                cur_content += r["result"]
                is_truncated = r["is_truncated"]
                yield r

    def batch_do(
        self,
        messages_list: Union[List[List[Dict]], List[QfMessages]],
        worker_num: Optional[int] = None,
        **kwargs: Any,
    ) -> BatchRequestFuture:
        """
        Batch perform chat-based language generation using user-supplied messages.

        Parameters:
          messages_list: List[Union[List[Dict], QfMessages]]:
            List of the messages list in the conversation. Please refer to
            `ChatCompletion.do` for more information of each messages.
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
        task_list = [
            partial(self.do, messages=messages, **kwargs) for messages in messages_list
        ]

        return self._batch_request(task_list, worker_num)

    async def abatch_do(
        self,
        messages_list: List[Union[List[Dict], QfMessages]],
        worker_num: Optional[int] = None,
        **kwargs: Any,
    ) -> List[Union[QfResponse, AsyncIterator[QfResponse]]]:
        """
        Async batch perform chat-based language generation using user-supplied messages.

        Parameters:
          messages_list: List[Union[List[Dict], QfMessages]]:
            List of the messages list in the conversation. Please refer to
            `ChatCompletion.do` for more information of each messages.
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
        tasks = [self.ado(messages=messages, **kwargs) for messages in messages_list]
        return await self._abatch_request(tasks, worker_num)

    def _generate_body(
        self, model: Optional[str], endpoint: str, stream: bool, **kwargs: Any
    ) -> JsonBody:
        """
        generate body
        """
        truncate_msg = kwargs["_auto_truncate"]
        del kwargs["_auto_truncate"]

        body = super()._generate_body(model, endpoint, stream, **kwargs)
        if not truncate_msg or len(body["messages"]) <= 1:
            return body

        # truncate the messages if the length is too long
        if model is not None and model in self._supported_models():
            model_info = self._supported_models()[model]
        else:
            default_model_info = self._supported_models()[self._default_model()]
            if endpoint == default_model_info.endpoint:
                model_info = default_model_info
            else:
                model_info = self._supported_models()[UNSPECIFIED_MODEL]

        if model_info.max_input_chars is not None:
            chars_limit = model_info.max_input_chars
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
