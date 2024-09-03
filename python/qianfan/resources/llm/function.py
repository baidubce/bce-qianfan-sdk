# Copyright (c) 2024 Baidu, Inc. All Rights Reserved.
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
import json
import re
from typing import Any, AsyncIterator, Dict, Iterator, List, Optional, Union

import qianfan.errors as errors
from qianfan.consts import Consts, DefaultValue
from qianfan.resources.llm.base import (
    UNSPECIFIED_MODEL,
    BaseResourceV1,
    BaseResourceV2,
)
from qianfan.resources.typing import QfLLMInfo, QfMessages, QfResponse

_DEFAULT_FUNCTIONS_ENHANCE_PROMPT = r"""接下来的所有对话中，你可以使用外部的工具来回答问题。
你必须按照规定的格式来使用工具，当你使用工具时，我会在下一轮对话给你工具调用结果，然后你应该根据实际结果判断是否需要进一步使用工具，或给出你的回答。
工具可能有多个，每个工具由名称、描述、参数组成，参数符合标准的json schema。

下面是工具列表:
{functions}

如果你需要使用外部工具，那么你的输出必须按照如下格式，只包含2行，不需要输出任何解释或其他无关内容:
Action: 使用的工具名称
Action Input: 使用工具的参数，json格式

如果你不需要使用外部工具，不需要输出Action和Action Input，请输出你的回答。
你的问题：{query}"""  # noqa

_DEFAULT_FUNCTIONS_SCHEMA_PROMPT = r"""名称：{name}
描述：{description}
参数：{parameters}
"""

_DEFAULT_FUNCTION_CALL_PROMPT = r"Action: {name}\nAction Input: {input}"

_SPLIT_FUNCTIONS_SCHEMAS = """\n-"""

_PROMPT_IDENTIFIER = "{}"

_RESPONSE_ACTION_PREFIX = "Action: "

_RESPONSE_ACTION_INPUT_PREFIX = "Action Input: "


class FunctionV2(BaseResourceV2):
    """
    QianFan Function is an agent for calling QianFan
    ChatCompletion with function call API.
    """

    def _api_path(self) -> str:
        return Consts.ChatV2API

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
        return "ernie-func-8k"


class BaseFunction:
    def _render_query(
        self, query: Dict[str, Any], messages: List[Dict], functions: List[Dict]
    ) -> None:
        functions_schemas = self._render_functions_prompt(functions)
        messages[0] = self._render_user_query_msg(
            messages[0], functions=functions_schemas
        )

        # render function message:
        for i, msg in enumerate(messages):
            if msg["role"] == "function":
                msg["role"] = "user"
                if "name" in msg:
                    msg.pop("name")
            elif msg["role"] == "assistant" and msg.get("function_call"):
                messages[i] = self._render_assistant_msg(msg)

        query["messages"] = messages
        if "functions" in query:
            query.pop("functions")

    def _render_assistant_msg(self, msg: Dict) -> Dict:
        function_call = msg.get("function_call", {})
        msg["content"] = self._render_prompt(
            _DEFAULT_FUNCTION_CALL_PROMPT,
            _PROMPT_IDENTIFIER,
            name=function_call.get("name"),
            input=function_call.get("arguments"),
        )
        msg.pop("function_call")
        return msg

    def _render_functions_prompt(self, functions: List[Dict]) -> str:
        functions_prompt = []
        for f in functions:
            functions_prompt.append(
                self._render_prompt(
                    _DEFAULT_FUNCTIONS_SCHEMA_PROMPT,
                    _PROMPT_IDENTIFIER,
                    name=f.get("name"),
                    description=f.get("description"),
                    parameters=json.dumps(f.get("parameters", {}), ensure_ascii=False),
                )
            )

        return _SPLIT_FUNCTIONS_SCHEMAS.join(functions_prompt)

    def _render_user_query_msg(self, msg: Dict, **kwargs: Any) -> Dict:
        return {
            "role": "user",
            "content": self._render_prompt(
                _DEFAULT_FUNCTIONS_ENHANCE_PROMPT,
                _PROMPT_IDENTIFIER,
                functions=kwargs.get("functions"),
                query=msg["content"],
            ),
        }

    def _render_prompt(
        self, prompt_template: str, identifier: str, **kwargs: Any
    ) -> str:
        from qianfan.resources.console.prompt import Prompt as PromptResource

        variables = PromptResource._extract_variables(prompt_template, identifier)

        def _render(_prompt: str, _vars: List[str], **kwargs: Any) -> str:
            left_id, right_id = PromptResource._split_identifier(identifier)
            for v in _vars:
                if v not in kwargs:
                    raise errors.InvalidArgumentError(
                        f"functions prompt variable `{v}` is not provided"
                    )
                _prompt = _prompt.replace(f"{left_id}{v}{right_id}", str(kwargs[v]))
            return _prompt

        return _render(prompt_template, variables, **kwargs)
        return "ernie-func-8k"


class Function(BaseResourceV1, BaseFunction):
    """
    QianFan Function is an agent for calling QianFan
    ChatCompletion with function call API.
    """

    def _self_supported_models(self) -> Dict[str, QfLLMInfo]:
        return self._local_models()

    def _local_models(self) -> Dict[str, QfLLMInfo]:
        """
        preset model list of Functions
        support model:
        - ERNIE-Functions-8K

        Args:
            None

        Returns:
            a dict which key is preset model and value is the endpoint

        """
        info_list = {
            "ERNIE-Functions-8K": QfLLMInfo(
                endpoint="/chat/ernie-func-8k",
                required_keys={"messages"},
                optional_keys={
                    "temperature",
                    "top_p",
                    "penalty_score",
                    "system",
                    "user_id",
                    "stop",
                    "max_output_tokens",
                    "enable_user_memory",
                    "user_memory_extract_level",
                },
                max_input_chars=11200,
                max_input_tokens=7168,
                input_price_per_1k_tokens=0.004,
                output_price_per_1k_tokens=0.008,
            ),
            UNSPECIFIED_MODEL: QfLLMInfo(
                endpoint="",
                required_keys={"messages"},
                optional_keys=set(),
            ),
        }

        return info_list

    @classmethod
    def _default_model(cls) -> str:
        """
        default model of functions calling

        Args:
            None

        Returns:
           "ERNIE-Functions-8K"

        """
        return "ERNIE-Functions-8K"

    def do(
        self,
        messages: Union[List[Dict], QfMessages],
        functions: List[Dict] = [],
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
          functions (List[Dict]):
            A list of functions that will be used in function calling.
          kwargs (Any):
            Additional keyword arguments that can be passed to customize the request.

        Example:
        ```
        func_list = [{
            "name": "function_name",
            "description": "description_of_function",
            "parameters":{
                "type":"object",
                "properties":{
                    "param1":{
                        "type":"string",
                        "description": "desc of params xxx"
                    }
                },
                "required":["param1"]
            }
        }]
        Function().do(messages = ..., functions=func_list)
        ```

        """
        if isinstance(messages, QfMessages):
            temp_messages = messages._to_list()
        else:
            temp_messages = messages
        for k in [
            "auto_concat_truncate",
            "truncated_continue_prompt",
            "truncate_overlong_msgs",
        ]:
            if k in kwargs:
                del kwargs[k]

        for k in ["request_id"]:
            if k in kwargs and kwargs.get(k) is None:
                del kwargs[k]

        if not functions:
            # 没有传入functions，不特殊处理，直接走普通的base_resource请求模式
            kwargs["messages"] = temp_messages
            return super()._do(**kwargs)
        self._render_query(query=kwargs, messages=temp_messages, functions=functions)

        resp = super()._do(**kwargs)
        if isinstance(resp, QfResponse):
            return self._convert_function_call_response(resp)
        elif isinstance(resp, Iterator):
            return self._convert_function_call_stream_response(resp)
        else:
            raise ValueError(f"Invalid type of response. {type(resp)}")

    def _convert_function_call_stream_response(
        self, iter: Iterator[QfResponse]
    ) -> Iterator[QfResponse]:
        not_match: Optional[bool] = None
        current_resp_result = ""
        last_message: Optional[QfResponse] = None
        for r in iter:
            # not match the function call return
            # return stream iterator
            last_message = r
            if not_match:
                yield r
                continue

            current_resp_result += r.get("result", "")
            # not match, read utils the whole result for parsing
            if not_match is False:
                continue
            action = re.search(f"{_RESPONSE_ACTION_PREFIX}(\w+)", current_resp_result)
            if action:
                not_match = False
            elif len(current_resp_result) > len(_RESPONSE_ACTION_PREFIX):
                r.body["result"] = current_resp_result
                not_match = True
                yield r

        action_input = re.search(
            f"{_RESPONSE_ACTION_INPUT_PREFIX}(.+)", current_resp_result
        )
        # match the function call
        if action and action_input:
            assert last_message is not None
            last_message.body["function_call"] = {
                "name": action.group(1),
                "arguments": action_input.group(1),
            }
            last_message.body["result"] = ""
            yield last_message

    async def _convert_function_call_stream_response_async(
        self, async_iter: AsyncIterator[QfResponse]
    ) -> AsyncIterator[QfResponse]:
        not_match: Optional[bool] = None
        current_resp_result = ""
        last_message: Optional[QfResponse] = None
        async for r in async_iter:
            last_message = r
            if not_match:
                yield r
                continue

            current_resp_result += r.get("result", "")
            if not_match is False:
                continue

            action = re.search(f"{_RESPONSE_ACTION_PREFIX}(\w+)", current_resp_result)
            if action:
                not_match = False
            elif len(current_resp_result) > len(_RESPONSE_ACTION_PREFIX):
                r.body["result"] = current_resp_result
                not_match = True
                yield r

        action_input = re.search(
            f"{_RESPONSE_ACTION_INPUT_PREFIX}(.+)", current_resp_result
        )
        if action and action_input:
            assert last_message is not None
            last_message.body["function_call"] = {
                "name": action.group(1),
                "arguments": action_input.group(1),
            }
            last_message.body["result"] = ""
            yield last_message

    def _convert_function_call_response(self, resp: QfResponse) -> QfResponse:
        # parse response content
        action_content = resp.body.get("result", "")
        action = re.search(f"{_RESPONSE_ACTION_PREFIX}(\w+)", action_content)
        action_input = re.search(f"{_RESPONSE_ACTION_INPUT_PREFIX}(.+)", action_content)

        # update QfResponse
        if action and action_input:
            resp.body["function_call"] = {
                "name": action.group(1),
                "arguments": action_input.group(1),
            }
            resp.body["result"] = ""
        return resp

    async def ado(
        self,
        messages: Union[List[Dict], QfMessages],
        functions: List[Dict] = [],
        **kwargs: Any,
    ) -> Union[QfResponse, AsyncIterator[QfResponse]]:
        """
        Perform chat-based language generation using user-supplied messages.

        Parameters:
          messages (Union[List[Dict], QfMessages]):
            A list of messages in the conversation including the one from system. Each
            message should be a dictionary containing 'role' and 'content' keys,
            representing the role (either 'user', or 'assistant') and content of the
            message, respectively. Alternatively, you can provide a QfMessages object
            for convenience.
          functions (List[Dict]):
            A list of functions that will be used in function calling.
          kwargs (Any):
            Additional keyword arguments that can be passed to customize the request.

        Example:
        ```
        func_list = [{
            "name": "function_name",
            "description": "description_of_function",
            "parameters":{
                "type":"object",
                "properties":{
                    "param1":{
                        "type":"string",
                        "description": "desc of params xxx"
                    }
                },
                "required":["param1"]
            }
        }]
        await Function().ado(messages = ..., functions=func_list)
        ```

        """
        if isinstance(messages, QfMessages):
            temp_messages = messages._to_list()
        else:
            temp_messages = messages
        for k in [
            "auto_concat_truncate",
            "truncated_continue_prompt",
            "truncate_overlong_msgs",
        ]:
            if k in kwargs:
                del kwargs[k]

        for k in ["request_id"]:
            if k in kwargs and kwargs.get(k) is None:
                del kwargs[k]

        if not functions:
            # 没有传入functions，不特殊处理，直接走普通的base_resource请求模式
            kwargs["messages"] = temp_messages
            return await super()._ado(**kwargs)
        self._render_query(query=kwargs, messages=temp_messages, functions=functions)

        resp = await super()._ado(**kwargs)
        if isinstance(resp, QfResponse):
            return self._convert_function_call_response(resp)
        elif isinstance(resp, AsyncIterator):
            return self._convert_function_call_stream_response_async(resp)
        else:
            raise ValueError(f"Invalid type of response. {type(resp)}")
