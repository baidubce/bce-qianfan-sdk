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

import os
import tempfile

from qianfan.components import Prompt
from qianfan.consts import PromptFrameworkType, PromptSceneType, PromptType


def test_init_remote_prompt():
    """
    Test init prompt from remote
    """
    prompt = Prompt(name="ut")
    assert prompt._mode == "remote"
    assert prompt.id is not None
    assert prompt.name == "ut"
    assert prompt.template == "example template {var1}"
    assert prompt.variables == ["var1"]
    assert prompt.type == PromptType.User
    assert prompt.scene_type == PromptSceneType.Text2Text
    assert prompt.framework_type == PromptFrameworkType.NotUse
    assert prompt.negative_template is None
    assert prompt.creator_name == "ut"
    assert prompt.identifier == "{}"
    assert len(prompt.labels) > 0
    assert prompt.labels[0].id == 150
    assert ("example template v1", None) == prompt.render(var1="v1")

    prompt = Prompt(name="txt2img")
    assert prompt._mode == "remote"
    assert prompt.id is not None
    assert prompt.name == "txt2img"
    assert prompt.template == "txt2img template {badvar} ((v1))"
    assert prompt.identifier == "(())"
    assert prompt.variables == ["v1"]
    assert prompt.type == PromptType.Preset
    assert prompt.scene_type == PromptSceneType.Text2Image
    assert prompt.framework_type == PromptFrameworkType.NotUse
    assert prompt.negative_template == "negative ((v3))"
    assert prompt.negative_variables == ["v3"]
    assert prompt.creator_name == "ut"
    assert len(prompt.labels) > 0
    assert prompt.labels[0].id == 188
    assert ("txt2img template {badvar} var1", "negative var3") == prompt.render(
        v1="var1", v3="var3"
    )


def test_init_local_prompt():
    """
    Test init prompt from local
    """
    prompt = Prompt(mode="local", template="example template {var1}")
    assert prompt._mode == "local"
    assert prompt.id is None
    assert prompt.name is None
    assert prompt.template == "example template {var1}"
    assert prompt.variables == ["var1"]
    assert prompt.type == PromptType.User
    assert prompt.scene_type == PromptSceneType.Text2Text
    assert prompt.framework_type == PromptFrameworkType.NotUse
    assert prompt.negative_template is None
    assert prompt.creator_name is None
    assert prompt.identifier == "{}"
    assert ("example template v1", None) == prompt.render(var1="v1")

    prompt = Prompt(
        name="txt2img",
        mode="local",
        template="txt2img template {badvar} ((v1))",
        scene_type=PromptSceneType.Text2Image,
        negative_template="negative template ((v3))",
        identifier="(())",
    )
    assert prompt._mode == "local"
    assert prompt.id is None
    assert prompt.name == "txt2img"
    assert prompt.template == "txt2img template {badvar} ((v1))"
    assert prompt.identifier == "(())"
    assert prompt.variables == ["v1"]
    assert prompt.negative_variables == ["v3"]
    assert prompt.scene_type == PromptSceneType.Text2Image
    assert (
        "txt2img template {badvar} var1",
        "negative template var3",
    ) == prompt.render(v1="var1", v3="var3")


def test_upload_prompt():
    """
    Test upload prompt
    """
    prompt = Prompt(mode="local", template="example template {var1}")
    prompt.name = "ut"
    assert prompt._mode == "local"
    assert prompt.id is None
    prompt.upload()
    # change to the id in mock response
    assert prompt.id == 732
    assert prompt._mode == "remote"

    prompt = Prompt(name="ut")
    assert prompt._mode == "remote"
    prompt.set_template("new template {h1} {h2}")
    assert prompt.template == "new template {h1} {h2}"
    assert prompt.variables == ["h1", "h2"]
    prompt.upload()
    # should upload and refresh the prompt
    # due to the mock server, prompt should be refreshed by the mock response
    assert prompt.id == 11827
    assert prompt.template == "example template {var1}"

    prompt = Prompt(name="txt2img")
    assert prompt._mode == "remote"
    prompt.identifier = "{}"
    prompt.set_template("new template {h1} {h2}")
    assert prompt.template == "new template {h1} {h2}"
    assert prompt.variables == ["h1", "h2"]
    prompt.set_negative_template("new negative template {h1} {h3}")
    assert prompt.negative_template == "new negative template {h1} {h3}"
    assert prompt.negative_variables == ["h1", "h3"]
    prompt.upload()
    # should upload and refresh the prompt
    # due to the mock server, prompt should be refreshed by the mock response
    assert prompt.id == 724
    assert prompt.template == "txt2img template {badvar} ((v1))"
    assert prompt.negative_template == "negative ((v3))"


def test_render():
    """
    test render prompt
    """
    p = Prompt(template="{v1}{v2}x {v3}", mode="local")
    assert p.render(v1="a", v2="3", v3="4") == ("a3x 4", None)
    assert p.render(v1="a", v2="", v3="") == ("ax ", None)

    p = Prompt(template="{v1}{{v2}}x {{v3}", identifier="{{}}", mode="local")
    assert p.variables == ["v2"]
    assert p.render(v1="a", v2="3", v3="4") == ("{v1}3x {{v3}", None)

    p = Prompt(template="{v1}{v2}x {v3}", identifier="{{}}", mode="local")
    assert p.variables == []
    assert p.render(v1="a", v2="3", v3="4") == ("{v1}{v2}x {v3}", None)

    p = Prompt(
        template="{v1}{v2}x {v3}", identifier="{}", variables=["v2", "v3"], mode="local"
    )
    assert p.variables == ["v2", "v3"]
    assert p.render(v1="a", v2="3", v3="4") == ("{v1}3x 4", None)


def test_delete():
    """
    test delete prompt
    """
    prompt = Prompt(name="ut")
    prompt.delete()
    assert prompt.id is None
    assert prompt._mode == "local"


def test_load_and_save():
    """
    test load and save prompt
    """
    template = "test template {var1}"
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_file = os.path.join(tmp_dir, "prompt.tpl")
        prompt = Prompt(template=template, mode="local")
        prompt.save_to_file(tmp_file)
        new_prompt = Prompt.from_file(tmp_file)
        assert new_prompt.template == template
        assert new_prompt.render(var1="test") == prompt.render(var1="test")
