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
    Unit test for Prompt
"""

from qianfan.consts import PromptFrameworkType, PromptSceneType, PromptType
from qianfan.resources import Prompt


def test_create_prompt():
    """
    Test create prompt
    """
    resp = Prompt.create(name="test name 1", template="test {var1} prompt {var2}")
    assert resp["_request"] == {
        "templateName": "test name 1",
        "templateContent": "test {var1} prompt {var2}",
        "templateVariables": "var1,var2",
        "variableIdentifier": "{}",
        "sceneType": 1,
        "frameworkType": 0,
    }
    result = resp["result"]
    assert "templateId" in result

    resp = Prompt.create(name="test name 2", template="empty prompt")
    assert resp["_request"] == {
        "templateName": "test name 2",
        "templateContent": "empty prompt",
        "templateVariables": "",
        "variableIdentifier": "{}",
        "sceneType": 1,
        "frameworkType": 0,
    }

    resp = Prompt.create(
        name="test name 3",
        template="{{x1}}other{{x2}}identifier{{x3}}",
        identifier="{{}}",
    )
    assert resp["_request"] == {
        "templateName": "test name 3",
        "templateContent": "{{x1}}other{{x2}}identifier{{x3}}",
        "templateVariables": "x1,x2,x3",
        "variableIdentifier": "{{}}",
        "sceneType": 1,
        "frameworkType": 0,
    }

    resp = Prompt.create(
        name="test name 4",
        template="{{x1}}custom{{x2}}identifier{{x3}}",
        identifier="{{}}",
        variables=["x1", "x3"],
    )
    assert resp["_request"] == {
        "templateName": "test name 4",
        "templateContent": "{{x1}}custom{{x2}}identifier{{x3}}",
        "templateVariables": "x1,x3",
        "variableIdentifier": "{{}}",
        "sceneType": 1,
        "frameworkType": 0,
    }

    resp = Prompt.create(
        name="test name 5",
        template="[[x1]]text2[[x2]]image[[x3]]{{r}}{6}",
        identifier="[[]]",
        scene=PromptSceneType.Text2Image,
        label_ids=[1, 2],
        framework=PromptFrameworkType.Fewshot,
        negative_template="[[x1]]negative[[x4]]((r))",
    )
    assert resp["_request"] == {
        "templateName": "test name 5",
        "templateContent": "[[x1]]text2[[x2]]image[[x3]]{{r}}{6}",
        "templateVariables": "x1,x2,x3",
        "variableIdentifier": "[[]]",
        "labelIds": [1, 2],
        "sceneType": 2,
        "frameworkType": 3,
        "negativeTemplateContent": "[[x1]]negative[[x4]]((r))",
        "negativeTemplateVariables": "x1,x4",
    }

    resp = Prompt.create(
        name="test name 6",
        template="[[x1]]text2[[x2]]image[[x3]]{{r}}{6}",
        identifier="[[]]",
        scene=PromptSceneType.Text2Image,
        label_ids=[1, 2],
        framework=PromptFrameworkType.Fewshot,
        negative_template="[[x1]]custom[[x4]]negative((r))",
        negative_variables=["x1"],
    )
    assert resp["_request"] == {
        "templateName": "test name 6",
        "templateContent": "[[x1]]text2[[x2]]image[[x3]]{{r}}{6}",
        "templateVariables": "x1,x2,x3",
        "variableIdentifier": "[[]]",
        "labelIds": [1, 2],
        "sceneType": 2,
        "frameworkType": 3,
        "negativeTemplateContent": "[[x1]]custom[[x4]]negative((r))",
        "negativeTemplateVariables": "x1",
    }


def test_render_prompt():
    """
    Test render prompt
    """
    resp = Prompt.info(id=11, var1="v1", var2="v2")
    assert resp["_request"] == {"id": "11", "var1": "v1", "var2": "v2"}
    assert "templateId" in resp["result"]
    assert "content" in resp["result"]


def test_update_prompt():
    """
    Test update prompt
    """
    resp = Prompt.update(id=1, name="test name")
    assert resp["_request"] == {
        "templateId": 1,
        "templateName": "test name",
    }
    result = resp["result"]
    assert "templateId" in result

    resp = Prompt.update(
        id=2,
        name="test name",
        label_ids=[1, 2],
        template="template{x1}",
        identifier="(())",
        negative_template="negative",
    )
    assert resp["_request"] == {
        "templateId": 2,
        "templateName": "test name",
        "labelIds": [1, 2],
        "templateContent": "template{x1}",
        "variableIdentifier": "(())",
        "negativeTemplateContent": "negative",
    }
    result = resp["result"]
    assert "templateId" in result


def test_delete_prompt():
    """
    Test delete prompt
    """
    resp = Prompt.delete(id=122)
    assert resp["_request"] == {
        "templateId": 122,
    }
    result = resp["result"]
    assert result is True


def test_list_prompts():
    """
    Test list prompts
    """
    resp = Prompt.list()
    assert resp["_request"] == {"labelIds": [], "offset": 0, "pageSize": 10}
    assert "items" in resp["result"]

    resp = Prompt.list(
        offset=10,
        page_size=20,
        name="test name",
        label_ids=[1, 2],
        type=PromptType.Preset,
    )
    assert resp["_request"] == {
        "offset": 10,
        "pageSize": 20,
        "name": "test name",
        "labelIds": [1, 2],
        "type": 1,
    }


def test_list_prompt_labels():
    """
    Test list prompt labels
    """
    resp = Prompt.list_labels()
    assert resp["_request"] == {"offset": 0, "pageSize": 10}
    assert "items" in resp["result"]

    resp = Prompt.list_labels(offset=10, page_size=20)
    assert resp["_request"] == {
        "offset": 10,
        "pageSize": 20,
    }
