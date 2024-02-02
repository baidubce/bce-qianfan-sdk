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
constants of evaluation
"""

QianfanRefereeEvaluatorDefaultMetrics: str = "综合得分"

QianfanRefereeEvaluatorDefaultSteps: str = """
1.仔细阅读所提供的问题，确保你理解问题的要求和背景。
2.仔细阅读所提供的标准答案，确保你理解问题的标准答案
3.阅读答案，并检查是否用词不当
4.检查答案是否严格遵照了题目的要求，包括答题方式、答题长度、答题格式等等。
"""
QianfanRefereeEvaluatorDefaultMaxScore: int = 5

QianfanRefereeEvaluatorPromptTemplate: str = """你是一个好助手。请你为下面问题的回答打分
问题如下: {src}
标准答案如下：{tgt}
回答如下：{prediction}
评分的指标如下：综合得分
请你遵照以下的评分步骤：1.仔细阅读所提供的问题，确保你理解问题的要求和背景。
2.仔细阅读所提供的标准答案，确保你理解问题的标准答案
3.阅读答案，并检查是否用词不当
4.检查答案是否严格遵照了题目的要求，包括答题方式、答题长度、答题格式等等。
根据答案的综合水平给出0到5的评分。如果答案存在明显的不合理之处，则应给出一个较低的评分。如果答案符合以上要求并且与参考答案含义相似，则应给出一个较高的评分。
你的回答模版如下:
评分: 此处只能回答整数评分
原因: 此处只能回答评分原因"""

LocalJudgeEvaluatorPromptTemplate: str = """
你是一名裁判员，负责为给定prompt的生成结果进行评分。

评价标准：

{criteria}

请你遵照以下的评分步骤：
{steps}


例子：

文档：

{prompt}

生成内容：

{response}

标准答案：（没有标准答案时，该项为空）

{reference}

评分要求：
根据生成内容的综合水平给出0到{max_score}之间的整数评分。
如果生成内容存在明显的不合理之处，则应给出一个较低的评分。
如果生成内容符合以上要求并且与参考答案含义相似，则应给出一个较高的评分

你的回答模版如下:
评分: 此处只能回答整数评分
原因: 此处只能回答评分原因
"""
