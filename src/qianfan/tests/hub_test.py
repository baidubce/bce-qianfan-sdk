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

from qianfan.components import Prompt, hub


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
