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

from typing import List

from qianfan.components.tool.base_tool import BaseTool, ToolParameter


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
                "test_param": {
                    "type": "string",
                    "description": "test param"
                }
            },
            "required": ["test_param"],
        }
    }


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
    assert parameter.to_json_schema() == {
        "type": "string",
        "description": "test param"
    }


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
                required=True
            )
        ]
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
                "required": ["nested_int_param"]
            }
        },
        "required": ["required_nested_param", "nested_object"]
    }
