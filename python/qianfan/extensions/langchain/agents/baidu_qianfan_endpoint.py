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

"""
    Qianfan agent base class and its implementations
"""

import json
from typing import Any, List, Optional, Sequence, Tuple, Union

from langchain.agents import BaseMultiActionAgent, BaseSingleActionAgent
from langchain.chat_models import QianfanChatEndpoint
from langchain.schema import (
    AgentAction,
    AgentFinish,
    AIMessage,
    BaseMessage,
    BasePromptTemplate,
    FunctionMessage,
    SystemMessage,
)
from langchain.schema.language_model import BaseLanguageModel
from langchain.tools import BaseTool, format_tool_to_openai_function

# langchain 新版本有部分逻辑迁移至 langchain_core
# 为了兼容老版本而 try catch
try:
    from langchain_core.callbacks.base import Callbacks
    from langchain_core.prompts import (
        ChatPromptTemplate,
        HumanMessagePromptTemplate,
        MessagesPlaceholder,
    )

    # notice:
    # 此处使用 langchain.pydantic_v1 是 langchain 依赖 pydantic 1.x 的兼容手段
    # 使 SDK 安装了 pydantic 2.x 时，agent 代码也能正常工作。请勿修改。
    from langchain_core.pydantic_v1 import root_validator
except ImportError:
    from langchain.callbacks.base import Callbacks
    from langchain.prompts import (
        ChatPromptTemplate,
        HumanMessagePromptTemplate,
        MessagesPlaceholder,
    )

    # 同上
    from langchain.pydantic_v1 import root_validator


def _convert_action_into_message(
    intermediate_steps: List[Tuple[AgentAction, str]]
) -> List[BaseMessage]:
    messages: List[BaseMessage] = []
    for step, tool_result in intermediate_steps:
        messages.append(
            AIMessage(
                content="",
                additional_kwargs={
                    "function_call": {
                        "name": step.tool,
                        "arguments": json.dumps(step.tool_input),
                    }
                },
            )
        )
        try:
            dicts = json.loads(tool_result)
        except Exception:
            ...
        if not isinstance(tool_result, dict):
            dicts = {"result": tool_result}

        messages.append(FunctionMessage(name=step.tool, content=json.dumps(dicts)))
    return messages


def _agent_input_keys() -> List[str]:
    return ["input"]


def _agent_validate_logical_core(values: dict) -> dict:
    """check if llm is valid"""
    if not isinstance(values["llm"], QianfanChatEndpoint):  # type: ignore
        raise ValueError("Only supported with QianfanChatEndpoint models.")
    if not (values["llm"].model == "ERNIE-Bot" or values["llm"].model == "ERNIE-Bot-4"):
        raise ValueError(
            f"Model could only be ERNIE-Bot or ERNIE-Bot-4, not {values['llm'].model}"
        )
    return values


def _prompt_template_generate_logical_core(
    system_prompt: Optional[SystemMessage], default_prompt: SystemMessage
) -> ChatPromptTemplate:
    system_prompt = system_prompt if system_prompt else default_prompt
    user_input_template = HumanMessagePromptTemplate.from_template("{input}")
    chat_history_template = MessagesPlaceholder(variable_name="history")
    return ChatPromptTemplate(
        messages=[system_prompt, user_input_template, chat_history_template],
        input_variables=["input", "history"],
    )


class QianfanSingleActionAgent(BaseSingleActionAgent):
    """single action implementation"""

    llm: BaseLanguageModel
    tools: Sequence[BaseTool]
    prompt: BasePromptTemplate

    @property
    def input_keys(self) -> List[str]:
        """input key"""
        return _agent_input_keys()

    @root_validator
    @classmethod
    def validate_llm(cls, values: dict) -> dict:
        """check if llm is valid"""
        return _agent_validate_logical_core(values)

    @classmethod
    def _generate_prompt_template(
        cls, system_prompt: Optional[SystemMessage]
    ) -> ChatPromptTemplate:
        return _prompt_template_generate_logical_core(
            system_prompt, cls._default_system_prompt()
        )

    @classmethod
    def from_system_prompt(
        cls,
        tools: List[BaseTool],
        llm: BaseLanguageModel,
        system_prompt: Optional[SystemMessage] = None,
    ) -> Any:
        """construct an agent"""
        return cls(
            llm=llm, tools=tools, prompt=cls._generate_prompt_template(system_prompt)
        )

    def plan(
        self,
        intermediate_steps: List[Tuple[AgentAction, str]],
        callbacks: Callbacks = None,
        **kwargs: Any,
    ) -> Union[AgentAction, AgentFinish]:
        """plan an action"""
        tool_history = _convert_action_into_message(intermediate_steps)
        messages = self.prompt.format_prompt(
            history=tool_history, **kwargs
        ).to_messages()
        result: BaseMessage = self.llm.predict_messages(
            messages, callbacks=callbacks, functions=self._wrapper_function, **kwargs
        )
        action = self._parse_message_to_action(result)

        assert isinstance(action, (AgentAction, AgentFinish))
        return action

    async def aplan(
        self,
        intermediate_steps: List[Tuple[AgentAction, str]],
        callbacks: Callbacks = None,
        **kwargs: Any,
    ) -> Union[AgentAction, AgentFinish]:
        """plan an action asynchronously"""
        tool_history = _convert_action_into_message(intermediate_steps)
        messages = self.prompt.format_prompt(
            history=tool_history, **kwargs
        ).to_messages()
        result: BaseMessage = await self.llm.apredict_messages(
            messages, callbacks=callbacks, functions=self._wrapper_function, **kwargs
        )
        action = self._parse_message_to_action(result)

        assert isinstance(action, (AgentAction, AgentFinish))
        return action

    @classmethod
    def _default_system_prompt(cls) -> SystemMessage:
        return SystemMessage(
            content=(
                "你是一个擅长使用工具以解决问题的智能助理，你应该使用工具逐步解决问题。"
                "在解决问题之前，你不需要和用户进行对话"
            )
        )

    @property
    def _wrapper_function(self) -> List[dict]:
        return [dict(format_tool_to_openai_function(t)) for t in self.tools]

    @classmethod
    def _parse_message_to_action(
        cls, result: BaseMessage
    ) -> Union[AgentAction, AgentFinish]:
        if result.content:
            return AgentFinish(
                return_values={"output": result.content}, log=str(result)
            )

        tool_json = result.additional_kwargs.get("function_call", {})
        if not tool_json:
            raise ValueError("empty function call value retrieved from service")
        tool_name = tool_json["name"]
        tool_inputs = json.loads(tool_json["arguments"])
        if "__arg1" in tool_inputs:
            tool_inputs = tool_inputs["__arg1"]
        else:
            tool_inputs = tool_inputs
        return AgentAction(tool=tool_name, tool_input=tool_inputs, log=str(result))


class QianfanMultiActionAgent(BaseMultiActionAgent):
    """multi action implementation"""

    llm: BaseLanguageModel
    tools: Sequence[BaseTool]
    prompt: BasePromptTemplate

    @property
    def input_keys(self) -> List[str]:
        """input key"""
        return _agent_input_keys()

    @root_validator
    @classmethod
    def validate_llm(cls, values: dict) -> dict:
        return _agent_validate_logical_core(values)

    @classmethod
    def _generate_prompt_template(
        cls, system_prompt: Optional[SystemMessage]
    ) -> ChatPromptTemplate:
        return _prompt_template_generate_logical_core(
            system_prompt, cls._default_system_prompt()
        )

    @classmethod
    def from_system_prompt(
        cls,
        tools: List[BaseTool],
        llm: BaseLanguageModel,
        system_prompt: Optional[SystemMessage] = None,
    ) -> Any:
        """construct an agent"""
        return cls(
            llm=llm, tools=tools, prompt=cls._generate_prompt_template(system_prompt)
        )

    def plan(
        self,
        intermediate_steps: List[Tuple[AgentAction, str]],
        callbacks: Callbacks = None,
        **kwargs: Any,
    ) -> Union[List[AgentAction], AgentFinish]:
        """plan an action"""
        tool_history = _convert_action_into_message(intermediate_steps)
        messages = self.prompt.format_prompt(
            history=tool_history, **kwargs
        ).to_messages()
        result: BaseMessage = self.llm.predict_messages(
            messages, callbacks=callbacks, functions=self._wrapper_function, **kwargs
        )
        action = self._parse_message_to_action(result)
        assert isinstance(action, (list, AgentFinish))
        return action

    async def aplan(
        self,
        intermediate_steps: List[Tuple[AgentAction, str]],
        callbacks: Callbacks = None,
        **kwargs: Any,
    ) -> Union[List[AgentAction], AgentFinish]:
        """plan an action asynchronously"""
        tool_history = _convert_action_into_message(intermediate_steps)
        messages = self.prompt.format_prompt(
            history=tool_history, **kwargs
        ).to_messages()
        result: BaseMessage = await self.llm.apredict_messages(
            messages, callbacks=callbacks, functions=self._wrapper_function, **kwargs
        )
        action = self._parse_message_to_action(result)
        assert isinstance(action, (list, AgentFinish))
        return action

    @classmethod
    def _default_system_prompt(cls) -> SystemMessage:
        return SystemMessage(
            content=(
                "你是一个擅长使用工具以解决问题的智能助理，"
                "你在解决用户问题时，应该一次性使用尽可能多的工具完成任务，"
                "在返回正确结果前无需与用户对话"
            )
        )

    @property
    def _wrapper_function(self) -> List[dict]:
        tool_selection = {
            "name": "tool_selection",
            "description": "需要采取的行动列表。",
            "parameters": {
                "title": "tool_selection",
                "description": "需要采取的行动列表。",
                "type": "object",
                "properties": {
                    "actions": {
                        "title": "actions",
                        "type": "array",
                        "description": "一系列需要执行的行动列表。",
                        "items": {
                            "title": "tool_call",
                            "type": "object",
                            "properties": {
                                # This is the action to take.
                                "action": {
                                    "title": "Action",
                                    "anyOf": [
                                        {
                                            "title": t.name,
                                            "type": "object",
                                            "properties": t.args,
                                            "description": t.description,
                                        }
                                        for t in self.tools
                                    ],
                                },
                            },
                            "required": ["action"],
                        },
                    }
                },
                "required": ["actions"],
            },
        }
        return [tool_selection]

    @classmethod
    def _parse_message_to_action(
        cls, result: BaseMessage
    ) -> Union[List[AgentAction], AgentFinish]:
        if result.content:
            return AgentFinish(
                return_values={"output": result.content}, log=str(result)
            )

        arg_str = result.additional_kwargs.get("function_call", {}).get("arguments", "")
        if not arg_str:
            raise ValueError("arguments retrieved from service is empty")
        action_list = json.loads(arg_str)["actions"]
        if not isinstance(action_list, list):
            raise TypeError("arguments isn't a list containing actions")

        actions = []
        for action in action_list:
            tool_name = action.get("action", "")
            action.pop("action")
            tool_inputs = action
            actions.append(AgentAction(tool=tool_name, tool_input=tool_inputs, log=""))
        return actions
