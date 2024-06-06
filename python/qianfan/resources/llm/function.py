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
from typing import Any, AsyncIterator, Dict, Iterator, List, Union

import qianfan.errors as errors
from qianfan.resources.llm.base import (
    UNSPECIFIED_MODEL,
    BaseResourceV1,
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


class Function(BaseResourceV1):
    """
    QianFan Function is an agent for calling QianFan
    ChatCompletion with function call API.
    """

    @classmethod
    def _supported_models(cls) -> Dict[str, QfLLMInfo]:
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
        functions: List[Dict],
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
        if len(functions) <= 0:
            raise errors.InvalidArgumentError(
                "functions should be a list of functions, "
                "each function is a dictionary with name and description."
            )
        if kwargs.get("stream") is True:
            raise errors.InvalidArgumentError("Function does not support stream mode.")

        if isinstance(messages, QfMessages):
            temp_messages = messages._to_list()
        else:
            temp_messages = messages

        functions_schemas = self._render_functions_prompt(functions)
        temp_messages[0] = self._render_user_query_msg(
            temp_messages[0], functions=functions_schemas
        )

        # render function message:
        for i, msg in enumerate(temp_messages):
            if msg["role"] == "function":
                msg["role"] = "user"
                msg.pop("name")
            elif msg["role"] == "assistant" and msg.get("function_call"):
                temp_messages[i] = self._render_assistant_msg(msg)

        kwargs["messages"] = temp_messages
        if "functions" in kwargs:
            kwargs.pop("functions")

        resp = super()._do(**kwargs)
        assert isinstance(resp, QfResponse)
        return self._convert_function_call_response(resp)

    def _convert_function_call_response(self, resp: QfResponse) -> QfResponse:
        # parse response content
        action_content = resp.body.get("result", "")
        action = re.search(r"Action: (\w+)", action_content)
        action_input = re.search(r"Action Input: (.+)", action_content)

        # update QfResponse
        if action and action_input:
            resp.body["function_call"] = {
                "name": action.group(1),
                "arguments": action_input.group(1),
            }
            resp.body["result"] = ""
        return resp

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

    async def ado(
        self,
        messages: Union[List[Dict], QfMessages],
        functions: List[Dict],
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
        if len(functions) <= 0:
            raise errors.InvalidArgumentError(
                "functions should be a list of functions, "
                "each function is a dictionary with name and description."
            )
        if kwargs.get("stream") is True:
            raise errors.InvalidArgumentError("Function does not support stream mode.")

        if isinstance(messages, QfMessages):
            temp_messages = messages._to_list()
        else:
            temp_messages = messages

        functions_schemas = self._render_functions_prompt(functions)
        temp_messages[0] = self._render_user_query_msg(
            temp_messages[0], functions=functions_schemas
        )
        # render function message:
        for i, msg in enumerate(temp_messages):
            if msg["role"] == "function":
                msg["role"] = "user"
                msg.pop("name")
            elif msg["role"] == "assistant" and msg.get("function_call"):
                temp_messages[i] = self._render_assistant_msg(msg)

        kwargs["messages"] = temp_messages
        if "functions" in kwargs:
            kwargs.pop("functions")

        resp = await super()._ado(**kwargs)
        assert isinstance(resp, QfResponse)
        return self._convert_function_call_response(resp)
