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

from dataclasses import dataclass
from typing import Dict, List, Literal, Optional, Tuple

from qianfan.components.hub.interface import HubSerializable
from qianfan.consts import PromptFrameworkType, PromptSceneType, PromptType
from qianfan.errors import InvalidArgumentError
from qianfan.resources.console.prompt import Prompt as PromptResource
from qianfan.utils import log_warn


@dataclass
class PromptLabel(object):
    id: int
    name: str
    color: str


class Prompt(HubSerializable):
    """
    Prompt
    """

    id: Optional[int] = None
    name: str
    template: str
    variables: List[str]
    identifier: Literal["{}", "{{}}", "[]", "[[]]", "()", "(())"]
    labels: List[PromptLabel]
    type: PromptType
    scene_type: PromptSceneType
    framework_type: PromptFrameworkType
    negative_template: Optional[str] = None
    negative_variables: Optional[List[str]] = None
    creator_name: Optional[str] = None
    _mode: str

    def __init__(
        self,
        name: str,
        mode: Literal["local", "remote"] = "remote",
        template: Optional[str] = None,
        identifier: Literal["{}", "{{}}", "[]", "[[]]", "()", "(())"] = "{}",
        variables: Optional[List[str]] = None,
        labels: List[PromptLabel] = [],
        type: PromptType = PromptType.User,
        scene_type: PromptSceneType = PromptSceneType.Text2Text,
        framework_type: PromptFrameworkType = PromptFrameworkType.NotUse,
        negative_template: Optional[str] = None,
        negative_variables: Optional[List[str]] = None,
        creator_name: Optional[str] = None,
    ) -> None:
        self._mode = mode
        # in `remote` mode, the object is initialized by name
        if mode == "remote":
            self._init_by_remote(name)
            # if the object is initialized by remote
            # other input attributes will be ignored
        elif mode == "local":
            # in `local` mode, the object is initialized by local provided attributes
            self.name = name
            if template is None:
                raise InvalidArgumentError("template is required if using local prompt")
            self.template = template
            self.identifier = identifier
            self.labels = labels
            self.type = type
            self.scene_type = scene_type
            self.framework_type = framework_type
            if variables is not None:
                self.variables = variables
            else:
                self.variables = PromptResource._extract_variables(template, identifier)
            self.negative_template = negative_template
            self.negative_variables = negative_variables
            self.creator_name = creator_name
        else:
            raise InvalidArgumentError(
                f"mode should be `local` or `remote`, got {mode}"
            )

    def _init_by_remote(self, name: str) -> None:
        resp = PromptResource.list(name=name, type=PromptType.User)
        prompt_info = None
        # try to find the prompt in user prompts
        for item in resp["result"]["items"]:
            if item["templateName"] == name:
                prompt_info = item
                break
        # if not found, try to find the prompt in preset prompts
        if prompt_info is None:
            resp = PromptResource.list(name=name, type=PromptType.Preset)
            for item in resp["result"]["items"]:
                if item["templateName"] == name:
                    prompt_info = item
                    break
        # if still not found, raise error
        if prompt_info is None:
            raise InvalidArgumentError(f"Prompt `{name}` does not exist")

        self.id = prompt_info["templateId"]
        self.name = prompt_info["templateName"]
        self.template = prompt_info["templateContent"]
        self.variables = prompt_info["templateVariables"].split(",")
        self.labels = [
            PromptLabel(label["labelId"], label["labelName"], label["color"])
            for label in prompt_info["labels"]
        ]
        self.identifier = prompt_info["variableIdentifier"]
        self.type = PromptType(prompt_info["type"])
        self.scene_type = PromptSceneType(prompt_info["sceneType"])
        self.framework_type = PromptFrameworkType(prompt_info["frameworkType"])
        self.creator_name = prompt_info["creatorName"]
        if self.scene_type == PromptSceneType.Text2Image:
            self.negative_template = prompt_info["negativeTemplateContent"]
            self.negative_variables = prompt_info["negativeTemplateVariables"].split(
                ","
            )

    def upload(self) -> None:
        """
        Upload the prompt to Qianfan.
        """
        # local prompt, create it
        if self._mode == "local" or self.id is None:
            resp = PromptResource.create(
                name=self.name,
                template=self.template,
                identifier=self.identifier,
                scene=self.scene_type,
                framework=self.framework_type,
                label_ids=[label.id for label in self.labels],
                negative_template=self.negative_template,
                negative_variables=self.negative_variables,
            )
            if not resp["success"]:
                raise InvalidArgumentError(
                    f"Failed to create prompt: {resp['message']['global']}"
                )
            self.id = resp["result"]["templateId"]
            self._mode = "remote"
        else:
            resp = PromptResource.update(
                id=self.id,
                name=self.name,
                label_ids=[label.id for label in self.labels],
                template=self.template,
                identifier=self.identifier,
                negative_template=self.negative_template,
            )
            if not resp["success"]:
                raise InvalidArgumentError(
                    f"Failed to update prompt: {resp['message']['global']}"
                )
            self._init_by_remote(self.name)

    def render(self, **kwargs: str) -> Tuple[str, Optional[str]]:
        """
        Render the prompt with given variables.
        """
        prompt = self.template
        left_id, right_id = PromptResource._split_identifier(self.identifier)
        for v in self.variables:
            if v not in kwargs:
                raise InvalidArgumentError(f"variable `{v}` is not provided")
            prompt = prompt.replace(f"{left_id}{v}{right_id}", kwargs[v])
        neg_prompt = None
        if (
            self.scene_type == PromptSceneType.Text2Image
            and self.negative_template is not None
        ):
            if self.negative_variables is None:
                self.negative_variables = []
            neg_prompt = self.negative_template
            for v in self.negative_variables:
                if v not in kwargs:
                    raise InvalidArgumentError(f"variable `{v}` is not provided")
                neg_prompt = neg_prompt.replace(f"{left_id}{v}{right_id}", kwargs[v])
        return prompt, neg_prompt

    def delete(self) -> None:
        """
        Delete the prompo from Qianfan.
        """
        if self._mode == "local" or self.id is None:
            log_warn("local prompt does not need to be deleted")
            return
        if self.type == PromptType.Preset:
            log_warn(f"preset prompt {self.name} cannot be deleted")
            return
        resp = PromptResource.delete(id=self.id)
        if not resp["success"]:
            raise InvalidArgumentError(
                f"Failed to delete prompt: {resp['message']['global']}"
            )

    def set_template(self, template: str) -> None:
        """
        Set the prompt's template.
        """
        self.template = template
        self.variables = PromptResource._extract_variables(template, self.identifier)

    def set_negative_template(self, template: str) -> None:
        """
        Set the prompt's negative template.
        """
        self.negative_template = template
        self.negative_variables = PromptResource._extract_variables(
            template, self.identifier
        )

    def _hub_serialize(self) -> Dict:
        return {
            "id": self.id,
            "name": self.name,
            "template": self.template,
            "identifier": self.identifier,
            "labels": [
                {"id": label.id, "name": label.name, "color": label.color}
                for label in self.labels
            ],
            "type": self.type.value,
            "sceneType": self.scene_type.value,
            "frameworkType": self.framework_type.value,
            "negativeTemplate": self.negative_template,
            "negativeVariables": self.negative_variables,
            "creatorName": self.creator_name,
            "mode": self._mode,
        }

    @classmethod
    def _hub_deserialize(cls, data: Dict) -> "Prompt":
        p = Prompt(
            mode="local",
            name=data["name"],
            template=data["template"],
            identifier=data["identifier"],
            labels=[
                PromptLabel(id=label["id"], name=label["name"], color=label["color"])
                for label in data["labels"]
            ],
            type=PromptType(data["type"]),
            scene_type=PromptSceneType(data["sceneType"]),
            framework_type=PromptFrameworkType(data["frameworkType"]),
            negative_template=data["negativeTemplate"],
            negative_variables=data["negativeVariables"],
            creator_name=data["creatorName"],
        )
        p.id = data["id"]
        p._mode = data["mode"]
        return p
