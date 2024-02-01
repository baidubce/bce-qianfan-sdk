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

from qianfan import Completion
from qianfan.common import Prompt
from qianfan.common.hub import hub
from qianfan.consts import PromptFrameworkType, PromptSceneType, PromptType


def test_init_remote_prompt():
    """
    Test init prompt from remote
    """
    prompt = hub.load("prompt/ut")
    assert isinstance(prompt, Prompt)
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

    prompt = hub.load("prompt/txt2img")
    assert isinstance(prompt, Prompt)
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
    prompt = Prompt(template="example template {var1}")
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
    prompt = Prompt(template="example template {var1}")
    prompt.name = "ut"
    assert prompt._mode == "local"
    assert prompt.id is None
    hub.push(prompt)
    # change to the id in mock response
    assert prompt.id.startswith("pt-")
    assert prompt._mode == "remote"

    prompt = hub.load("prompt/ut")
    assert isinstance(prompt, Prompt)
    assert prompt._mode == "remote"
    prompt.set_template("new template {h1} {h2}")
    assert prompt.template == "new template {h1} {h2}"
    assert prompt.variables == ["h1", "h2"]
    hub.push(prompt)
    # should upload and refresh the prompt
    # due to the mock server, prompt should be refreshed by the mock response
    assert prompt.id.startswith("pt-")

    prompt = hub.load("prompt/txt2img")
    assert isinstance(prompt, Prompt)
    assert prompt._mode == "remote"
    prompt.identifier = "{}"
    prompt.set_template("new template {h1} {h2}")
    assert prompt.template == "new template {h1} {h2}"
    assert prompt.variables == ["h1", "h2"]
    prompt.set_negative_template("new negative template {h1} {h3}")
    assert prompt.negative_template == "new negative template {h1} {h3}"
    assert prompt.negative_variables == ["h1", "h3"]
    hub.push(prompt)
    # should upload and refresh the prompt
    # due to the mock server, prompt should be refreshed by the mock response
    assert prompt.id.startswith("pt-")


def test_render():
    """
    test render prompt
    """
    p = Prompt(template="{v1}{v2}x {v3}")
    assert p.render(v1="a", v2="3", v3="4") == ("a3x 4", None)
    assert p.render(v1="a", v2="", v3="") == ("ax ", None)

    p = Prompt(template="{v1}{{v2}}x {{v3}", identifier="{{}}")
    assert p.variables == ["v2"]
    assert p.render(v1="a", v2="3", v3="4") == ("{v1}3x {{v3}", None)

    p = Prompt(template="{v1}{v2}x {v3}", identifier="{{}}")
    assert p.variables == []
    assert p.render(v1="a", v2="3", v3="4") == ("{v1}{v2}x {v3}", None)

    p = Prompt(template="{v1}{v2}x {v3}", identifier="{}", variables=["v2", "v3"])
    assert p.variables == ["v2", "v3"]
    assert p.render(v1="a", v2="3", v3="4") == ("{v1}3x 4", None)

    p = Prompt(template="{v1} {v2}")
    assert p.variables == ["v1", "v2"]
    assert p.render(v1=1, v2={}) == ("1 {}", None)


def test_delete():
    """
    test delete prompt
    """
    prompt = hub.load("prompt/ut")
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
        prompt = Prompt(template=template)
        prompt.save_to_file(tmp_file)
        new_prompt = Prompt.from_file(tmp_file)
        assert new_prompt.template == template
        assert new_prompt.render(var1="test") == prompt.render(var1="test")


def test_framework():
    """
    test prompt framework
    """
    # Basic 类型
    basic_prompt = Prompt.base_prompt(
        prompt="帮我写一个年终总结",
        background="今年个人业绩情况为{var}。",
        additional_data="要去做演讲，风格要简约。",
        output_schema="输出内容要有成绩总结、遗留问题、改进措施和未来规划4项。",
    )
    assert (
        basic_prompt
        == "指令:帮我写一个年终总结\n背景信息:今年个人业绩情况为{var}。"
        "\n补充数据:要去做演讲，风格要简约。\n输出格式:输出内容要有成绩总结、"
        "遗留问题、改进措施和未来规划4项。"
    )

    basic_prompt = Prompt.base_prompt(
        prompt="帮我写一个年终总结",
    )
    assert basic_prompt == "指令:帮我写一个年终总结\n\n\n"  # multiple \n is required

    # CRISPE 类型
    crispe_prompt = Prompt.crispe_prompt(
        capacity="你现在是一个资深律师。",
        insight="最近你接了一个财务侵占的官司，涉案金额{money}元，你是受害人的辩护律师。",
        statement="请帮忙出一个法律公告，警示被告尽快偿还非法侵占的财务。",
        personality="公告内容要严谨严肃专业。",
        experiment="公告内容不宜超过800字。",
    )
    assert (
        crispe_prompt
        == "能力与角色：你现在是一个资深律师。"
        "\n背景信息：最近你接了一个财务侵占的官司，涉案金额{money}元，"
        "你是受害人的辩护律师。\n指令：请帮忙出一个法律公告，"
        "警示被告尽快偿还非法侵占的财务。\n输出风格：公告内容要严谨严肃专业。"
        "\n输出范围：公告内容不宜超过800字。"
    )
    crispe_prompt = Prompt.crispe_prompt(
        insight="最近你接了一个财务侵占的官司，涉案金额{money}元，你是受害人的辩护律师。",
        statement="请帮忙出一个法律公告，警示被告尽快偿还非法侵占的财务。",
    )
    assert (
        crispe_prompt
        == "背景信息：最近你接了一个财务侵占的官司，涉案金额{money}元，"
        "你是受害人的辩护律师。\n指令：请帮忙出一个法律公告，"
        "警示被告尽快偿还非法侵占的财务。"
    )

    # Fewshot 类型
    fewshot_prompt = Prompt.fewshot_prompt(
        prompt="现在在做一个数学计算游戏，请根据下述规则回答最后一个示例的问题",
        examples=[("1 2", "3"), ("2 3", "5"), ("3 4", "")],
    )
    assert (
        fewshot_prompt
        == "现在在做一个数学计算游戏，请根据下述规则回答最后一个示例的问题\n\n输入:1"
        " 2\n输出:3\n\n输入:2 3\n输出:5\n\n输入:3 4\n输出:"
    )
    fewshot_prompt = Prompt.fewshot_prompt(
        examples=[("1 2", "3"), ("2 3", "5"), ("3 4", "")],
    )
    assert fewshot_prompt == "输入:1 2\n输出:3\n\n输入:2 3\n输出:5\n\n输入:3 4\n输出:"


def test_optimize():
    prompt = Prompt(template="test template {var1}")
    optimized = prompt.optimize()
    assert optimized.template == "optimized prompt"


def test_evaluate():
    prompts = [Prompt(f"test{i} {{arg}}") for i in range(2)]
    scenes = [
        {"args": {"arg": f"arg{i}"}, "expected": f"expected{i}"} for i in range(3)
    ]
    client = Completion()
    eval_res = Prompt.evaluate(prompts, scenes, client)
    for i, res in enumerate(eval_res):
        assert res.prompt.template == f"test{i} {{arg}}"
        for j, scene in enumerate(res.scene):
            assert scene["expected_target"] == f"expected{j}"
            assert scene["new_prompt"] == f"test{i} arg{j}"
            assert scene["variables"] == {"arg": f"arg{j}"}
            assert scene["new_prompt"] in scene["response"]
        assert res.summary == f"response_{i}"
