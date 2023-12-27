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
base tool definition
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel
from qianfan.utils.utils import assert_package_installed


class ToolParameter(BaseModel):
    """
    Tool parameters, used to define the inputs when calling a tool and
    to describe the parameters needed when calling the tool to the model.
    """

    name: str
    """Name of the parameter."""
    type: str
    """
    Type of the parameter, corresponding to the types in JSON schema, 
    such as string, integer, object, array.
    """
    description: Optional[str] = None
    """
    Description of the parameter, 
    can include the function of the parameter and format requirements
    """
    properties: Optional[List["ToolParameter"]] = None
    """
    When the type of the parameter is object, 
    this defines the list of properties for the object.
    """
    required: Optional[bool] = False
    """Whether this parameter must be provided."""

    def to_json_schema(self) -> Dict[str, Any]:
        """
        Converts the parameter to a json schema.
        :return: json schema
        """
        schema: Dict[str, Any] = {
            "type": self.type,
        }

        if self.description:
            schema["description"] = self.description

        if self.properties:
            schema["properties"] = {
                prop.name: prop.to_json_schema() for prop in self.properties
            }
            required_properties = [
                prop.name for prop in self.properties if prop.required
            ]
            if len(required_properties) > 0:
                schema["required"] = required_properties

        return schema

    @staticmethod
    def from_pydantic_v1_schema(schema: Dict[str, Any]) -> "ToolParameter":
        """
        Converts a pydantic v1 model into a tool parameter.
        :param schema: pydantic model schema
        :return: tool parameter
        """
        name = schema["title"]
        parameter_type = schema["type"]
        description = schema.get("description", None)
        properties = None

        if "properties" in schema:
            properties = []
            for prop_name, prop_schema in schema["properties"].items():
                prop = ToolParameter.from_pydantic_v1_schema(prop_schema)
                prop.name = prop_name
                properties.append(prop)

            required_properties = schema.get("required", [])
            for prop in properties:
                prop.required = prop.name in required_properties

        return ToolParameter(
            name=name,
            type=parameter_type,
            description=description,
            properties=properties,
        )


class BaseTool:
    """
    Base class for tools,
    used to define the basic information and running method of a tool.
    Tools must be implemented based on this class,
    and must define the name, description, parameter list and implement the run method.
    """

    name: str
    """Name of the tool, needs to be clear, concise, and unique."""
    description: str
    """
    Description of the tool, 
    used to describe the functionality of the tool to the model.
    """
    parameters: List[ToolParameter]
    """
    List of parameters for the tool, 
    describing the parameters needed when invoking the tool to the model.
    """

    def run(self, parameters: Any = None) -> Any:
        """
        Runs the tool.
        :param parameters: The input parameters for the tool
        :return: The output result of the tool
        """
        pass

    def to_function_call_schema(self) -> Dict[str, Any]:
        """
        Converts the tool into a function call's json schema.
        :return: json schema
        """
        root_parameter = ToolParameter(
            name="root", type="object", properties=self.parameters
        )
        return {
            "name": self.name,
            "description": self.description,
            "parameters": root_parameter.to_json_schema(),
        }

    @staticmethod
    def from_langchain_tool(langchain_tool: Any) -> "BaseTool":
        assert_package_installed("langchain")
        from langchain.tools.base import BaseTool as LangchainBaseTool

        if not isinstance(langchain_tool, LangchainBaseTool):
            raise TypeError(
                "tool must be an instance of langchain.tools.base.BaseTool, got"
                f" {type(langchain_tool)}"
            )

        root_parameter = ToolParameter.from_pydantic_v1_schema(
            langchain_tool.get_input_schema().schema()
        )
        root_properties = root_parameter.properties if root_parameter.properties else []

        class Tool(BaseTool):
            name = langchain_tool.name
            description = langchain_tool.description
            parameters = root_properties

            def run(self, parameters: Any = None) -> Any:
                return langchain_tool._run(**parameters)

        return Tool()
