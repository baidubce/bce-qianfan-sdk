import json
import re
from typing import Any, List, Tuple, Union

from langchain.agents import BaseSingleActionAgent
from langchain.callbacks.base import Callbacks
from langchain.schema import (
    AgentAction,
    AgentFinish,
    AIMessage,
    BaseMessage,
    HumanMessage,
)
from langchain.schema.language_model import BaseLanguageModel
from langchain.tools import BaseTool

INITIAL_PROMPT = """
在接下来的所有对话中，你可以使用外部的工具来回答问题。
你必须按照规定的格式来使用工具，当你使用工具时，我会在下一轮对话给你工具调用结果，然后你应该根据实际结果判断是否需要进一步使用工具，或给出你的回答。
工具可能有多个，每个工具由名称、描述、参数组成，参数符合标准的json schema。

下面是工具列表:
{tool_list}
如果你需要使用外部工具，那么你的输出必须按照如下格式，只包含2行，不需要输出任何解释或其他无关内容:
Action: 使用的工具名称
Action Input: 使用工具的参数，json格式

如果你不需要使用外部工具，不需要输出Action和Action Input，请输出你的回答。

如果你明白了，请直接回答"好的"，然后让我们开始。
"""


class QianfanZeroShotAgent(BaseSingleActionAgent):
    tools: List[BaseTool]
    llm: BaseLanguageModel

    def _generate_initial_prompt(self) -> str:
        tool_string = ""
        for tool in self.tools:
            tool_string += (
                "名称: {tool_name}\n"
                "描述: {tool_description}\n"
                '参数: {{"type": "object", "properties": {tool_args_dict}}}\n'
                "-\n".format(
                    tool_name=tool.name,
                    tool_description=tool.description,
                    tool_args_dict=tool.args,
                )
            )
        return INITIAL_PROMPT.format(tool_list=tool_string[:-2]).replace("'", '"')

    def _convert_intermediate_steps_into_message(
        self, steps: List[Tuple[AgentAction, str]], user_input: str
    ) -> List[BaseMessage]:
        messages = [
            HumanMessage(content=self._generate_initial_prompt()),
            AIMessage(content="好的"),
            HumanMessage(content=user_input),
        ]
        for action, tool_result in steps:
            messages += [
                AIMessage(
                    content="Action: {}\nAction Input: {}".format(
                        action.tool, action.tool_input
                    )
                ),
                HumanMessage(content=tool_result),
            ]
        return messages

    def _parse_output(
        self, return_message: BaseMessage
    ) -> Union[AgentAction, AgentFinish]:
        exp = re.match(r"^Action: (.*?)\nAction Input: (.*)$", return_message.content)
        if not exp or len(exp.groups()) == 0:
            return AgentFinish(
                return_values={"output": return_message.content},
                log=str(return_message.additional_kwargs),
            )
        if len(exp.groups()) != 2:
            raise ValueError("incorrect group counter: " + str(len(exp.groups())))

        print(f"\ntool used: {exp.group(1)}\ntool input: {exp.group(2)}")
        return AgentAction(
            tool=exp.group(1),
            tool_input=json.loads(exp.group(2).replace("'", '"')),
            log="",
        )

    def plan(
        self,
        intermediate_steps: List[Tuple[AgentAction, str]],
        callbacks: Callbacks = None,
        **kwargs: Any,
    ) -> Union[AgentAction, AgentFinish]:
        messages = self._convert_intermediate_steps_into_message(
            intermediate_steps, **kwargs
        )
        return self._parse_output(self.llm.predict_messages(messages))

    async def aplan(
        self,
        intermediate_steps: List[Tuple[AgentAction, str]],
        callbacks: Callbacks = None,
        **kwargs: Any,
    ) -> Union[AgentAction, AgentFinish]:
        messages = self._convert_intermediate_steps_into_message(
            intermediate_steps, **kwargs
        )
        return self._parse_output(await self.llm.apredict_messages(messages))

    @property
    def input_keys(self) -> List[str]:
        return ["user_input"]
