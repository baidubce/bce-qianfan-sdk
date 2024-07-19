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
    Unit test for Tool
"""
from typing import List, Optional, Type

import qianfan
from qianfan.common.tool.baidu_search_tool import BaiduSearchTool
from qianfan.common.tool.base_tool import BaseTool, ToolParameter
from qianfan.utils.utils import check_package_installed


def test_tool_base():
    class TestTool(BaseTool):
        name: str = "test_tool"
        description: str = "test tool"
        parameters: List[ToolParameter] = [
            ToolParameter(
                name="test_param",
                type="string",
                description="test param",
                required=True,
            )
        ]

        def run(self, parameters=None):
            pass

    tool = TestTool()
    assert tool.name == "test_tool"
    assert tool.description == "test tool"
    assert tool.parameters[0] == ToolParameter(
        name="test_param",
        type="string",
        description="test param",
        required=True,
    )


def test_tool_run():
    class TestTool(BaseTool):
        name: str = "test_tool"
        description: str = "test tool"
        parameters: List[ToolParameter] = [
            ToolParameter(
                name="test_param",
                type="string",
                description="test param",
                required=True,
            )
        ]

        def run(self, parameters=None):
            return "run test_param " + parameters["test_param"]

    tool = TestTool()
    assert tool.run({"test_param": "value"}) == "run test_param value"


def test_tool_to_function_call_schema():
    class TestTool(BaseTool):
        name: str = "test_tool"
        description: str = "test tool"
        parameters: List[ToolParameter] = [
            ToolParameter(
                name="test_param",
                type="string",
                description="test param",
                required=True,
            )
        ]

        def __init__(self):
            pass

        def run(self, parameters=None):
            return parameters["test_param"]

    tool = TestTool()
    assert tool.to_function_call_schema() == {
        "name": "test_tool",
        "description": "test tool",
        "parameters": {
            "type": "object",
            "properties": {
                "test_param": {"type": "string", "description": "test param"}
            },
            "required": ["test_param"],
        },
    }


def test_tool_from_langchain_tool():
    if not check_package_installed("langchain"):
        return

    from langchain.tools.base import BaseTool as LangchainBaseTool

    from qianfan.utils.pydantic import BaseModel, Field

    class CalculatorToolSchema(BaseModel):
        a: int = Field(description="a description")
        b: int = Field(description="b description")
        prefix: Optional[str] = Field(description="prefix description")

    class CalculatorTool(LangchainBaseTool):
        name: str = "calculator"
        description: str = "calculator description"
        args_schema: Type[BaseModel] = CalculatorToolSchema

        def _run(self, a: int, b: int, prefix: Optional[str] = None):
            return a + b if prefix is None else prefix + str(a + b)

    tool = BaseTool.from_langchain_tool(CalculatorTool())
    assert tool.name == "calculator"
    assert tool.description == "calculator description"
    assert len(tool.parameters) == 3
    assert tool.parameters[0] == ToolParameter(
        name="a", type="integer", description="a description", required=True
    )
    assert tool.parameters[1] == ToolParameter(
        name="b", type="integer", description="b description", required=True
    )
    assert tool.parameters[2] == ToolParameter(
        name="prefix", type="string", description="prefix description", required=False
    )
    assert tool.run(tool_input={"a": 1, "b": 2}) == 3
    assert tool.run(tool_input={"a": 1, "b": 2, "prefix": "result: "}) == "result: 3"


def test_tool_from_langchain_func_tool():
    if not check_package_installed("langchain"):
        return

    from langchain_core.tools import StructuredTool as LangchainTool

    from qianfan.utils.pydantic import BaseModel, Field

    def hello(a: str, b: str) -> str:
        return f"hello {a} {b}"

    class FuncToolSchema(BaseModel):
        a: str = Field(description="a description")
        b: str = Field(description="b description")

    tool = BaseTool.from_langchain_tool(
        LangchainTool.from_function(
            func=hello,
            name="hello",
            description="hello description",
            args_schema=FuncToolSchema,
        )
    )

    assert tool.name == "hello"
    assert tool.description == "hello description"
    assert len(tool.parameters) == 2
    assert tool.parameters[0] == ToolParameter(
        name="a", type="string", description="a description", required=True
    )
    assert tool.parameters[1] == ToolParameter(
        name="b", type="string", description="b description", required=True
    )
    assert tool.run(tool_input={"a": "1", "b": "2"}) == "hello 1 2"


def test_tool_from_langchain_decorator_tool():
    if not check_package_installed("langchain"):
        return

    from langchain.tools.base import tool

    @tool
    def hello_tool(
        a: str,
        b: str,
    ) -> str:
        """Say hello"""
        return f"hello {a} {b}"

    tool = BaseTool.from_langchain_tool(hello_tool)

    assert tool.name == "hello_tool"
    assert tool.description in [
        "hello_tool(a: str, b: str) -> str - Say hello",
        "Say hello",
    ]
    assert len(tool.parameters) == 2
    assert tool.parameters[0] == ToolParameter(name="a", type="string", required=True)
    assert tool.parameters[1] == ToolParameter(name="b", type="string", required=True)
    assert tool.run(tool_input={"a": "1", "b": "2"}) == "hello 1 2"


def test_tool_to_langchain_tool():
    if not check_package_installed("langchain"):
        return

    class TestTool(BaseTool):
        name: str = "test_tool"
        description: str = "test tool"
        parameters: List[ToolParameter] = [
            ToolParameter(
                name="test_param",
                type="string",
                description="test param",
                required=True,
            )
        ]

        def run(self, **parameters):
            return parameters["test_param"]

    tool = TestTool()
    langchain_tool = tool.to_langchain_tool()
    assert langchain_tool.name == "test_tool"
    assert langchain_tool.description == "test tool"

    tool_schema = langchain_tool.get_input_schema().schema()
    model_title = tool_schema["title"]
    assert langchain_tool.get_input_schema().schema() == {
        "title": model_title,
        "type": "object",
        "properties": {
            "test_param": {
                "description": "test param",
                "title": "Test Param",
                "type": "string",
            }
        },
        "required": ["test_param"],
    }

    assert tool.run(**{"test_param": "value"}) == "value"
    assert langchain_tool.invoke({"test_param": "value"}) == "value"


def test_complex_args_tool_to_langchain_tool():
    if not check_package_installed("langchain"):
        return

    class ComplexTestTool(BaseTool):
        name: str = "test_tool"
        description: str = "test tool"
        parameters: List[ToolParameter] = [
            ToolParameter(
                name="required_string",
                type="string",
                description="required string",
                required=True,
            ),
            ToolParameter(
                name="required_integer",
                type="integer",
                description="required integer",
                required=True,
            ),
            ToolParameter(
                name="optional_number",
                type="number",
                description="optional number",
                required=False,
            ),
            ToolParameter(
                name="required_boolean",
                type="boolean",
                description="required boolean",
                required=True,
            ),
            ToolParameter(
                name="required_object",
                type="object",
                description="required object",
                properties=[
                    ToolParameter(
                        name="required_nested_string",
                        type="string",
                        description="required nested string",
                        required=True,
                    ),
                ],
                required=True,
            ),
            ToolParameter(
                name="optional_array",
                type="array",
                description="optional array",
                required=False,
            ),
            ToolParameter(
                name="optional_invalid_type",
                type="invalid_type",
                description="optional invalid type",
                required=False,
            ),
        ]

        def run(self, **parameters):
            return (
                parameters["required_integer"] if parameters["required_boolean"] else 0
            )

    tool = ComplexTestTool()
    langchain_tool = tool.to_langchain_tool()

    assert langchain_tool.name == "test_tool"
    assert langchain_tool.description == "test tool"

    tool_schema = langchain_tool.get_input_schema().schema()
    model_title = tool_schema["title"]
    object_model_title = list(tool_schema["definitions"])[0]
    assert langchain_tool.get_input_schema().schema() == {
        "title": model_title,
        "type": "object",
        "properties": {
            "required_string": {
                "description": "required string",
                "title": "Required String",
                "type": "string",
            },
            "required_integer": {
                "description": "required integer",
                "title": "Required Integer",
                "type": "integer",
            },
            "optional_number": {
                "description": "optional number",
                "title": "Optional Number",
                "type": "number",
            },
            "required_boolean": {
                "description": "required boolean",
                "title": "Required Boolean",
                "type": "boolean",
            },
            "required_object": {
                "allOf": [{"$ref": "#/definitions/" + object_model_title}],
                "description": "required object",
                "title": "Required Object",
            },
            "optional_array": {
                "description": "optional array",
                "title": "Optional Array",
                "type": "array",
                "items": {},
            },
            "optional_invalid_type": {
                "description": "optional invalid type",
                "title": "Optional Invalid Type",
            },
        },
        "required": [
            "required_string",
            "required_integer",
            "required_boolean",
            "required_object",
        ],
        "definitions": {
            object_model_title: {
                "properties": {
                    "required_nested_string": {
                        "description": "required nested string",
                        "title": "Required Nested String",
                        "type": "string",
                    }
                },
                "required": ["required_nested_string"],
                "title": object_model_title,
                "type": "object",
            }
        },
    }

    args_one = {
        "required_string": "required_string",
        "required_integer": 1,
        "required_boolean": True,
        "required_object": {"required_nested_string": "required_nested_string"},
    }
    args_zero = {
        "required_string": "required_string",
        "required_integer": 1,
        "required_boolean": False,
        "required_object": {"required_nested_string": "required_nested_string"},
    }
    assert tool.run(**args_one) == 1
    assert tool.run(**args_zero) == 0
    assert langchain_tool.invoke(args_one) == 1
    assert langchain_tool.invoke(args_zero) == 0


def test_parameter_base():
    parameter = ToolParameter(
        name="test_param",
        type="string",
        description="test param",
        required=True,
    )
    assert parameter.name == "test_param"
    assert parameter.type == "string"
    assert parameter.description == "test param"
    assert parameter.required


def test_parameter_to_json_schema():
    parameter = ToolParameter(
        name="test_param",
        type="string",
        description="test param",
    )
    assert parameter.to_json_schema() == {"type": "string", "description": "test param"}


def test_nested_parameter_to_json_schema():
    parameter = ToolParameter(
        name="test_param",
        type="object",
        description="test param",
        properties=[
            ToolParameter(
                name="required_nested_param",
                type="string",
                description="required nested param",
                required=True,
            ),
            ToolParameter(
                name="nested_param",
                type="string",
                description="nested param",
                required=False,
            ),
            ToolParameter(
                name="nested_object",
                type="object",
                description="nested object",
                properties=[
                    ToolParameter(
                        name="nested_int_param",
                        type="integer",
                        description="nested int param",
                        required=True,
                    ),
                ],
                required=True,
            ),
        ],
    )
    assert parameter.to_json_schema() == {
        "type": "object",
        "description": "test param",
        "properties": {
            "required_nested_param": {
                "type": "string",
                "description": "required nested param",
            },
            "nested_param": {
                "type": "string",
                "description": "nested param",
            },
            "nested_object": {
                "type": "object",
                "description": "nested object",
                "properties": {
                    "nested_int_param": {
                        "type": "integer",
                        "description": "nested int param",
                    }
                },
                "required": ["nested_int_param"],
            },
        },
        "required": ["required_nested_param", "nested_object"],
    }


def test_baidu_search_tool():
    tool = BaiduSearchTool(with_reference=True)
    res = tool.run(**{"search_query": "上海天气"})
    assert (
        res["summary"]
        == "**上海今天天气是晴转阴，气温在-4℃到1℃之间，风向无持续风向，"
        "风力小于3级，空气质量优**^[1]^。"
    )
    assert res["reference"] == [
        {
            "index": 1,
            "url": "http://www.weather.com.cn/weather/101020100.shtml",
            "title": "上海天气预报_一周天气预报",
        },
        {
            "index": 2,
            "url": "https://m.tianqi.com/shanghai/15/",
            "title": "上海天气预报15天_上海天气预报15天查询,上海未来15天天 ...",
        },
    ]

    tool = BaiduSearchTool()
    res = tool.run(**{"search_query": "上海天气"})
    assert (
        res
        == "**上海今天天气是晴转阴，气温在-4℃到1℃之间，风向无持续风向，"
        "风力小于3级，空气质量优**^[1]^。"
    )

    tool = BaiduSearchTool(with_reference=True)
    res = tool.run(**{"search_query": "no_search"})
    assert res["reference"] == []

    client = qianfan.Completion()
    tool = BaiduSearchTool(client=client, with_reference=True)
    res = tool.run(**{"search_query": "上海天气"})
    assert (
        res["summary"]
        == "**上海今天天气是晴转阴，气温在-4℃到1℃之间，风向无持续风向，"
        "风力小于3级，空气质量优**^[1]^。"
    )
    assert res["reference"] == [
        {
            "index": 1,
            "url": "http://www.weather.com.cn/weather/101020100.shtml",
            "title": "上海天气预报_一周天气预报",
        },
        {
            "index": 2,
            "url": "https://m.tianqi.com/shanghai/15/",
            "title": "上海天气预报15天_上海天气预报15天查询,上海未来15天天 ...",
        },
    ]
