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
Prompt API
"""
import re
from typing import Any, List, Optional, Tuple

from qianfan.consts import (
    Consts,
    PromptFrameworkType,
    PromptSceneType,
    PromptType,
)
from qianfan.errors import InvalidArgumentError
from qianfan.resources.console.utils import console_api_request
from qianfan.resources.typing import Literal, QfRequest


class Prompt(object):
    """
    Class for Prompt API
    """

    @classmethod
    @console_api_request
    def create(
        cls,
        name: str,
        template: str,
        identifier: Literal["{}", "{{}}", "[]", "[[]]", "()", "(())"] = "{}",
        scene: PromptSceneType = PromptSceneType.Text2Text,
        framework: PromptFrameworkType = PromptFrameworkType.NotUse,
        variables: Optional[List[str]] = None,
        label_ids: Optional[List[int]] = None,
        negative_template: Optional[str] = None,
        negative_variables: Optional[List[str]] = None,
        **kwargs: Any,
    ) -> QfRequest:
        """
        Creates a prompt template.

        Parameters:
          name (str):
            A descriptive name for the prompt template.
          template (str):
            The main text of the prompt template.
          identifier (Literal["{}", "{{}}", "[]", "[[]]", "()", "(())"]):
            The identifier pattern to be used for variable replacement in the template.
          scene (PromptSceneType):
            The type of prompt scene, e.g., Text2Text/Text2Image.
          framework (PromptFrameworkType):
            The framework to be used for prompt generation.
          variables (Optional[List[str]]):
            List of variables used in the template. If not provided, sdk will
            automatically find variables in the template. The variables only support
            English, numbers, and underscores (_), and cannot start with a number. They
            must be between 2 and 30 characters in length.
          label_ids (Optional[List[int]]):
            List of label IDs associated with the prompt.
          negative_template (Optional[str]):
            An optional negative example template. Only available when scene is
            Text2Image.
          negative_variables (Optional[List[str]]):
            List of variables for the negative example. Only available when scene is
            Text2Image.
          kwargs (Any):
            Additional keyword arguments that can be passed to customize the request.

        Returns:
          QfRequest: An object representing the prompt request.

        Note:
        The `@console_api_request` decorator is applied to this method, enabling it to
        send the generated QfRequest and return a QfResponse to the user.

        Usage:
        ```python
        prompt_request = Prompt.create(
            name="MyPrompt",
            template="Generate a sentence with {object}.",
            identifier="{}",
            scene=PromptSceneType.Text2Text,
            framework=PromptFrameworkType.NotUse,
            variables=["object"],
            label_ids=[1, 2],
            negative_template="Avoid using {profanity} in the sentence.",
            negative_variables=["profanity"],
            custom_arg="value"  # Additional keyword arguments can be included.
        )
        ```

        API Doc: https://cloud.baidu.com/doc/WENXINWORKSHOP/s/Hlp7waib4
        """
        req = QfRequest(method="POST", url=Consts.PromptCreateAPI)
        req.json_body = {
            "templateName": name,
            "templateContent": template,
            "variableIdentifier": identifier,
            "sceneType": scene.value,
            "frameworkType": framework.value,
            **kwargs,
        }
        # if user does not provide variables
        # we will extract them from the template
        if variables is None:
            variables = cls._extract_variables(template, identifier)
        req.json_body["templateVariables"] = ",".join(variables)
        if label_ids:
            req.json_body["labelIds"] = label_ids
        # following fields are only available when scene is Text2Image
        if scene == PromptSceneType.Text2Image:
            if negative_template:
                req.json_body["negativeTemplateContent"] = negative_template
            # if user does not provide variables
            # we will extract them from the template
            if negative_variables is None:
                negative_variables = (
                    cls._extract_variables(negative_template, identifier)
                    if negative_template is not None
                    else []
                )
            req.json_body["negativeTemplateVariables"] = ",".join(negative_variables)
        return req

    @classmethod
    @console_api_request
    def info(cls, id: int, **kwargs: Any) -> QfRequest:
        """
        Renders a prompt template and retrieves template details.

        This method is responsible for rendering a prompt template and obtaining
        details about the template.

        Parameters:
          id (int):
            The ID of the prompt template to render.
          kwargs (Any):
            The value of the variables to be used for variable replacement in the
            template.

        Returns:
          QfRequest:
            An object representing the request for rendering the prompt template.

        Note:
          The `@console_api_request` decorator is applied to this method, enabling it to
          send the generated QfRequest and return a QfResponse to the user.

        API Doc: https://cloud.baidu.com/doc/WENXINWORKSHOP/s/Olp7ysef9
        """
        req = QfRequest(method="POST", url=Consts.PromptInfoAPI)
        req.json_body = {"id": str(id), **kwargs}
        return req

    @classmethod
    @console_api_request
    def update(
        cls,
        id: int,
        name: Optional[str] = None,
        label_ids: Optional[List[int]] = None,
        template: Optional[str] = None,
        identifier: Optional[Literal["{}", "{{}}", "[]", "[[]]", "()", "(())"]] = None,
        negative_template: Optional[str] = None,
        **kwargs: Any,
    ) -> QfRequest:
        """
        Update information for a prompt template.

        This method is responsible for updating various attributes of a prompt template
        identified by the provided ID.

        Parameters:
          id (int):
            The ID of the prompt template to update.
          name (Optional[str]):
            The new name for the prompt template.
          label_ids (Optional[List[int]]):
            The updated list of label IDs associated with the prompt template.
          template (Optional[str]):
            The modified template for the prompt.
          identifier (Optional[Literal["{}", "{{}}", "[]", "[[]]", "()", "(())"]]):
            The updated identifier format for the prompt.
          negative_template (Optional[str]):
            The revised negative template for the prompt.
          kwargs (Any):
            Additional keyword arguments that can be passed to customize the request.

        Returns:
          QfRequest:
            An instance of QfRequest representing the update request.

        Note:
        The `@console_api_request` decorator is applied to this method, enabling it to
        send the generated QfRequest and return a QfResponse to the user.

        API Doc: https://cloud.baidu.com/doc/WENXINWORKSHOP/s/plp7tp3kx
        """
        req = QfRequest(method="POST", url=Consts.PromptUpdateAPI)
        req.json_body = {"templateId": id, **kwargs}
        if name is not None:
            req.json_body["templateName"] = name
        if label_ids:
            req.json_body["labelIds"] = label_ids
        if identifier:
            req.json_body["variableIdentifier"] = identifier
        if template:
            req.json_body["templateContent"] = template
        if negative_template:
            req.json_body["negativeTemplateContent"] = negative_template
        return req

    @classmethod
    @console_api_request
    def delete(cls, id: int, **kwargs: Any) -> QfRequest:
        """
        Deletes a prompt template.

        This method is responsible for deleting a prompt template based on the
        specified template ID.

        Parameters:
          id (int):
            The ID of the prompt template to delete.
          kwargs (Any):
            Additional keyword arguments that can be passed to customize the request.

        Returns:
          QfRequest:
            An instance of the QfRequest class representing the API request.

        Note:
        The `@console_api_request` decorator is applied to this method, enabling it to
        send the generated QfRequest and return a QfResponse to the user.

        API Doc: https://cloud.baidu.com/doc/WENXINWORKSHOP/s/Hlp7tri81
        """
        req = QfRequest(method="POST", url=Consts.PromptDeleteAPI)
        req.json_body = {"templateId": id, **kwargs}
        return req

    @classmethod
    @console_api_request
    def list(
        cls,
        offset: int = 0,
        page_size: int = 10,
        name: Optional[str] = None,
        label_ids: List[int] = [],
        type: Optional[PromptType] = None,
        **kwargs: Any,
    ) -> QfRequest:
        """
        Retrieves a list of prompt templates.

        This method is responsible for retrieving a list of prompt templates based on
        the specified parameters.

        Parameters:
          offset (int):
            The index from which to start retrieving prompt templates. Default is 0.
          page_size (int):
            The number of prompt templates to retrieve per page. Default is 10.
          name (Optional[str]):
            A filter for prompt templates by name.
          label_ids (List[int]):
            A list of label IDs to filter prompt templates.
          type (Optional[PromptType]):
            A filter for prompt templates by type.
          kwargs (Any):
            Additional keyword arguments that can be passed to customize the request.

        Returns:
          QfRequest:
            An object representing the request to retrieve prompt templates.

        Note:
        The `@console_api_request` decorator is applied to this method, enabling it to
        send the generated QfRequest and return a QfResponse to the user.

        API Doc: https://cloud.baidu.com/doc/WENXINWORKSHOP/s/ulp7tycbq
        """
        req = QfRequest(method="POST", url=Consts.PromptListAPI)
        req.json_body = {
            "offset": offset,
            "pageSize": page_size,
            "labelIds": label_ids,
            **kwargs,
        }
        if name is not None:
            req.json_body["name"] = name
        if type:
            req.json_body["type"] = type.value
        return req

    @classmethod
    @console_api_request
    def list_labels(
        cls, offset: int = 0, page_size: int = 10, **kwargs: Any
    ) -> QfRequest:
        """
        Retrieves a list of labels for prompt templates.

        This method is responsible for retrieving a list of labels. Labels provide
        information about the categories or attributes associated with each template.

        Parameters:
          offset (int):
            The offset for paginating through the list of labels. Default is 0.
          page_size (int):
            The number of labels to include in each page. Default is 10.
          kwargs (Any):
            Additional keyword arguments that can be passed to customize the request.

        Returns:
          QfRequest:
            An instance of the QfRequest class representing the API request.

        Note:
        The `@console_api_request` decorator is applied to this method, enabling it to
        send the generated QfRequest and return a QfResponse to the user.

        API Doc: https://cloud.baidu.com/doc/WENXINWORKSHOP/s/zlp7u6inp
        """
        req = QfRequest(method="POST", url=Consts.PromptLabelListAPI)
        req.json_body = {"offset": offset, "pageSize": page_size, **kwargs}
        return req

    @classmethod
    def _extract_variables(cls, template: str, identifier: str) -> List[str]:
        """
        extract variables from template
        """
        variables = []
        left_identifier, right_identifier = cls._split_identifier(identifier)

        # find all variables between identifiers
        vars = re.findall(
            "{}(.*?){}".format(re.escape(left_identifier), re.escape(right_identifier)),
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

    @classmethod
    def _split_identifier(cls, identifier: str) -> Tuple[str, str]:
        """
        split identifier into left and right part
        """
        left_id = identifier[: len(identifier) // 2]
        right_id = identifier[len(identifier) // 2 :]
        return left_id, right_id
