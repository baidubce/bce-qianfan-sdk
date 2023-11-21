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

from qianfan.resources.console.prompt import Prompt as PromptResource
from typing import List, Optional, Literal, Tuple
from dataclasses import dataclass
from qianfan.consts import PromptFrameworkType, PromptSceneType, PromptType
from qianfan.errors import InvalidArgumentError
from qianfan.resources.typing import QfResponse
import re


@dataclass
class PromptLabel(object):
    id: int
    name: str
    color: str


class Prompt(object):
    """
    Prompt
    """

    id: Optional[int]
    name: str
    template: str
    variables: List[str]
    identifier: Literal["{}", "{{}}", "[]", "[[]]", "()", "(())"]
    labels: List[PromptLabel]
    type: PromptType
    scene_type: PromptSceneType
    framework_type: PromptFrameworkType
    negative_template: Optional[str]
    negative_variables: Optional[List[str]]

    def __init__(
        self,
        id: Optional[int] = None,
        name: Optional[str] = None,
        template: Optional[str] = None,
        identifier: Literal["{}", "{{}}", "[]", "[[]]", "()", "(())"] = "{}",
        variables: Optional[List[str]] = None,
        labels: List[PromptLabel] = [],
        type: PromptType = PromptType.User,
        scene_type: PromptSceneType = PromptSceneType.Text2Text,
        framework_type: PromptFrameworkType = PromptFrameworkType.NotUse,
        negative_template: Optional[str] = None,
        negative_variables: Optional[List[str]] = None,
    ) -> None:
        # when id is provided, the object is initialized by id
        if id is not None:
            resp = PromptResource.detail(id)
            self._init_by_remote_response(resp)
            # if the object is initialized by id
            # other input attributes will be ignored
            return
        # when id is not provided, the object is initialized by local provided attributes
        required_attrs = [name, template]
        for attr in required_attrs:
            if attr is None:
                raise InvalidArgumentError(
                    f"{attr} is required for Prompt if id is not provided"
                )
        self.name = name
        self.template = template
        self.identifier = identifier
        self.labels = labels
        self.type = type
        self.scene_type = scene_type
        self.framework_type = framework_type
        if variables is not None:
            self.variables = variables
        else:
            self.variables = self._extract_variable(template, identifier)
        self.negative_template = negative_template
        self.negative_variables = negative_variables

    def _init_by_remote_response(self, response: QfResponse) -> None:
        prompt_info = response["result"]
        self.id = prompt_info["templateId"]
        self.name = prompt_info["templateName"]
        self.template = prompt_info["templateContent"]
        self.variables = prompt_info["templateVariables"].split(",")
        self.labels = [
            PromptLabel(l["lableId"], l["lableName"], l["color"])
            for l in prompt_info["labels"]
        ]
        self.identifier = prompt_info["variableIdentifier"]
        self.type = PromptType(prompt_info["type"])
        self.scene_type = PromptSceneType(prompt_info["sceneType"])
        self.framework_type = PromptFrameworkType(prompt_info["frameworkType"])
        self.negative_template = prompt_info["negativeTemplate"]
        self.negative_variables = prompt_info["negativeVariables"].split(",")

    @classmethod
    def _extract_variable(cls, template: str, identifier: str) -> List[str]:
        variables = []
        left_identifier, right_identifier = cls._split_identifier(identifier)

        # find all variables between identifiers
        vars = re.findall(
            "{}(.*){}".format(re.escape(left_identifier), re.escape(right_identifier)),
            template,
        )
        # and check if they are valid variable names
        for v in vars:
            if not re.match(r"^[a-zA-Z_]([a-zA-Z0-9_]){1,29}$", v):
                raise InvalidArgumentError(
                    f"Found invalid variable name `{v}` in template. Variables only"
                    " support English, numbers, and underscores (_), and cannot start"
                    " with a number. They must be between 2 and 30 characters in"
                    " length."
                )
            variables.append(v)
        return variables

    def upload(self) -> None:
        """
        Upload the prompt to Qianfan.
        """
        # local prompt, create it
        if self.id is None:
            resp = PromptResource.create(
                name=self.name,
                template=self.template,
                identifier=self.identifier,
                scene=self.scene_type,
                framework=self.framework_type,
                label_ids=[l.id for l in self.labels],
                negative_template=self.negative_template,
                negative_variables=self.negative_variables,
            )
            self.id = resp["result"]["templateId"]
        else:
            resp = PromptResource.update(
                id=self.id,
                name=self.name,
                label_ids=[l.id for l in self.labels],
                template=self.template,
                identifier=self.identifier,
                negative_template=self.negative_template,
            )

    @classmethod
    def _split_identifier(cls, identifier: str) -> Tuple[str, str]:
        left_id = identifier[: len(identifier) // 2]
        right_id = identifier[len(identifier) // 2 :]
        return left_id, right_id

    def render(self, **kwargs: str) -> str:
        """
        Render the prompt with given variables.
        """
        s = self.template
        left_id, right_id = self._split_identifier(self.identifier)
        for v in self.variables:
            if v not in kwargs:
                raise InvalidArgumentError(f"Variable `{v}` is missing")
            s = s.replace(f"{left_id}{v}{right_id}", kwargs[v])
        return s

    def delete(self) -> None:
        """
        Delete the prompo from Qianfan.
        """
        PromptResource.delete(id=self.id)
