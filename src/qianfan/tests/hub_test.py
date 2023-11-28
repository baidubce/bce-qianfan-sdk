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
    Unit test for Hub
"""

import os
import tempfile

from qianfan.components import Prompt, PromptLabel, hub
from qianfan.consts import PromptFrameworkType, PromptType


def test_prompt_hub():
    """
    test prompt hub
    """
    p = Prompt(name="ut")
    s = hub.save(p)
    new_p = hub.load(s)
    assert isinstance(new_p, Prompt)
    assert new_p._mode == "local"
    assert new_p.name == p.name
    assert new_p.framework_type == p.framework_type
    assert new_p.type == p.type
    assert new_p.labels == p.labels
    assert new_p.variables == p.variables
    assert new_p.negative_template == p.negative_template

    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_file = os.path.join(tmp_dir, "prompt.json")
        p = Prompt(name="txt2img_ut")
        hub.save(p, path=tmp_file)
        new_p = hub.load(path=tmp_file)
        assert isinstance(new_p, Prompt)
        assert new_p._mode == "local"
        assert new_p.name == p.name
        assert new_p.framework_type == p.framework_type
        assert new_p.type == p.type
        assert new_p.labels == p.labels
        assert new_p.variables == p.variables
        assert new_p.negative_template == p.negative_template

    p = hub.load(url="http://127.0.0.1:8866/mock/hub/prompt")
    assert isinstance(p, Prompt)
    assert p.name == "穿搭灵感"
    assert p.variables == ["style", "gender"]
    assert p.labels[0] == PromptLabel(id=1734, name="生活助手", color="#2468F2")
    assert p.type == PromptType(1)
    assert p.framework_type == PromptFrameworkType.NotUse
