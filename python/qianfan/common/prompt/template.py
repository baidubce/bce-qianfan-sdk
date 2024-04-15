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

# APO 用于表示期望输入输出的模版
PROMPT_OPTIMIZE_SAMPLE_TMPL = """**我尝试的输入**：
{{input}}

**我期望得到的输出**：
{{expect}}

**模型的输出是**：
{{response}}"""

# APO 在没有期望输出的时候表示模型输入输出的模版
PROMPT_OPTIMIZE_SAMPLE_WO_OUTPUT_TMPL = """**我尝试的输入**：
{{input}}

**模型的输出是**：
{{response}}"""

# APO 用于获得模型反馈的模版
PROMPT_OPTIMIZE_FEEDBACK_TMPL = """我正在编写prompt

**我现在的prompt是**：
{{current_prompt}}

{{samples}}

===

根据我期望得到的输出和模型的输出，告诉我几个理由为什么这个 prompt 并不能很好的完成这个任务"""

# APO 用于更新 prompt 的模版
PROMPT_OPTIMIZE_UPDATE_TMPL = """我正在编写prompt

**我现在的prompt是**：
{{current_prompt}}

{{samples}}

**但是存在这些问题**：
{{feedback}}

===

基于以上问题和期望的输出，为我编写一个新的 prompt，涉及的变量用 {{variables}} 表示，整个prompt由<START>和<END>包裹：
"""

# 精简 prompt 的模版
PROMPT_SIMPLIFY_TMPL = """我当前正在编写的prompt是：

{{current_prompt}}

===

请根据我的需求，使用涉及的变量（用 {{variables}} 表示）来编写一个新的prompt，整个prompt由<START>和<END>包裹。新的prompt需要满足以下要求：

1. 结构清晰，精简长度；
2. 去除冗余信息，只保留与任务直接相关的信息；
3. 避免重复内容，确保每个部分都有其独特的意义和作用。
"""
