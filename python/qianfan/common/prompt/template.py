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

# disable line too long lint error in this file
# ruff: noqa: E501

PROMPT_OPTIMIZE_SAMPLE_TMPL = """**我尝试的输入**：
{{input}}

**我期望得到的输出**：
{{expect}}

**模型的输出是**：
{{response}}"""

PROMPT_OPTIMIZE_FEEDBACK_TMPL = """我正在编写prompt

**我现在的prompt是**：
{{current_prompt}}

{{samples}}

===

根据我期望得到的输出和模型的输出，告诉我几个理由为什么这个 prompt 并不能很好的完成这个任务"""

PROMPT_OPTIMIZE_UPDATE_TMPL = """我正在编写prompt

**我现在的prompt是**：
{{current_prompt}}

{{samples}}

**但是存在这些问题**：
{{feedback}}

===

基于以上问题和期望的输出，为我编写一个新的 prompt，涉及的变量用 {{variables}} 表示，整个prompt由<START>和<END>包裹：
"""
