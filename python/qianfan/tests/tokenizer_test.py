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
    Unit test for Tokenizer
"""

from qianfan import Tokenizer


def test_count_token_local():
    cases = [
        ("hello world 1 2 3", 5),
        ("你好呀", 1),
        ("你好hello哈哈world 1 2 3", 7),
        (" 你好 123 哈哈1！  \t 123 Hello world", 7),
    ]
    for text, count in cases:
        assert Tokenizer.count_tokens(text, mode="local") == count


def test_count_token_remote():
    prompt = "test prompt"
    assert Tokenizer.count_tokens(prompt, mode="remote") == 97575 + len(
        prompt
    )  # magic number
