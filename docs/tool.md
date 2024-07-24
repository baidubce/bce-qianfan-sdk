# Tool

为了方便将大模型与外部工具集成，千帆SDK提供了一套Tool框架。Tool可以类比成一个函数，它能够被Agent理解并使用，作为LLM与外部世界交互的工具。

基本流程是：Agent控制LLM，根据名称和描述判断用户的输入是否需要使用某个工具，如果确定需要使用一个工具，则进一步生成工具需要的参数，然后Agent使用参数调用对应的执行函数，并将执行函数的结果返回给LLM，再由LLM总结输出，最终返回给用户。

此外，SDK的Tool框架提供了一套转换方法，可以对LangChain等常见框架的Tool进行双向转换，以便集成其他生态。

## Tool类

Tool有两个核心类：

BaseTool：工具的基础类，用于定义工具的基本信息和运行方法。每个工具都必须基于此类实现，并定义名称、描述、参数列表以及实现run方法。

- **name**: 一个非常简短、清晰的名称，就像函数名那样。例如：baidu_search。
- **description**: 工具的描述，解释其功能和用途。例如：使用百度搜索引擎，在互联网上检索任何实时最新的相关信息。
- **parameters**: 调用这个Tool需要的参数，注意，参数应该和执行函数的入参一致。例如：search_query -> 搜索的关键词或短语。
- **run**: 接收参数并执行Tool对应的动作，然后返回执行结果。

ToolParameter：用于定义工具参数，包括参数的名称、类型、描述、属性以及是否为必需参数。

- **name**: 参数的名称。
- **description**: 参数的描述，可以包含其功能和格式要求。
- **type**: 参数的数据类型，如string、integer、object等，对应JSON schema中的类型。
- **properties**: 当参数类型为object时，定义该对象的属性列表。
- **required**: 表示参数是否必须提供。

## 定义工具

下面是一个简单的示例，用于定义并实现一个控制智能家居的工具。

light_switch工具用于控制智能电灯的开关，它接收一个switch的boolean参数用于表示开关状态，然后，我们在工具的run方法中实现控制逻辑。

```python
from typing import List
from qianfan.common.tool.base_tool import ToolParameter, BaseTool

class LightSwitchTool(BaseTool):
    name: str = "light_switch"
    description: str = "控制智能电灯的开关"
    parameters: List[ToolParameter] = [
        ToolParameter(
            name="switch",
            type="boolean",
            description="开关状态",
            required=True,
        )
    ]

    def run(self, parameters):
        # 此处编写控制逻辑
        return "灯已打开" if parameters["switch"] else "灯已关闭"
```

你可以在实例化一个工具类后直接运行它。

```python
light_switch_tool = LightSwitchTool()
print(light_switch_tool.run({"switch": True}))
```

在这个示例中，你应该会得到以下输出。

```
灯已打开
```

## 与外部能力集成

Tool类提供了以下方法：

- **to_function_call_schema**：将Tool转换为调用function call的JSON Schema。
- **to_langchain_tool**：将Tool转换为适配Langchain框架的Tool，可以被Langchain Agent直接调用。
- **from_langchain_tool**：这是一个静态方法，可以将Langchain框架的Tool实例转换为千帆SDK的Tool。

我们将开发完毕的LightSwitchTool实例化，随后调用to_langchain_tool方法来转换为Langchain的Tool，然后创建LLM和Agent，并传入Tool，最后运行。

```python
import os
from langchain.agents import AgentExecutor
from langchain_community.chat_models import QianfanChatEndpoint
from qianfan.extensions.langchain.agents import QianfanSingleActionAgent

os.environ["QIANFAN_AK"] = "此处填写你的AK"
os.environ["QIANFAN_SK"] = "此处填写你的SK"
tools = [LightSwitchTool().to_langchain_tool()]

llm = QianfanChatEndpoint(model="ERNIE-3.5-8K")
agent = QianfanSingleActionAgent.from_system_prompt(tools, llm)
agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

print(agent_executor.run("帮我关闭电灯"))
```

在这个示例中，你应该会得到以下输出。

```
content='' additional_kwargs={'id': 'as-6harkfa2rn', 'object': 'chat.completion', 'created': 1704699483, 'result': '', 'is_truncated': False, 'need_clear_history': False, 'function_call': {'name': 'light_switch', 'arguments': '{"switch":false}'}, 'finish_reason': 'function_call', 'usage': {'prompt_tokens': 108, 'completion_tokens': 25, 'total_tokens': 133}}

content='根据你的请求，我已经帮你关闭了电灯。如果你需要打开电灯，请告诉我。' additional_kwargs={'id': 'as-ctg359ensw', 'object': 'chat.completion', 'created': 1704699485, 'result': '根据你的请求，我已经帮你关闭了电灯。如果你需要打开电灯，请告诉我。', 'is_truncated': False, 'need_clear_history': False, 'finish_reason': 'normal', 'usage': {'prompt_tokens': 134, 'completion_tokens': 19, 'total_tokens': 153}}

> Finished chain.

好的，我已经帮您关闭了电灯。如果您需要再次打开电灯，请告诉我。
```
