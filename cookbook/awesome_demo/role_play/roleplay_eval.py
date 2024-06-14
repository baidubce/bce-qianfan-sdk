from qianfan.evaluation.evaluator import LocalEvaluator
from qianfan import ChatCompletion, Embedding
from qianfan.dataset import Dataset
from qianfan.common.prompt.prompt import Prompt
from qianfan.utils.pydantic import Field
import numpy as np
from cachetools import cached

from typing import Optional, Union, Any, Dict, List
import re
import json


def _convert_str_to_int(str_score: str) -> int:
    try:
        x = re.findall("\d+", str_score)
        return int(x[0])
    except:
        return 0


embedding = Embedding()


@cached(cache={})
def get_qianfan_embedding(content: str) -> np.array:
    return np.array(embedding.do([content]).body["data"][0]["embedding"])


class RolePlayEvaluator(LocalEvaluator):
    model: Optional[ChatCompletion] = Field(default=None, description="model object")
    metric_name: str = Field(default="", description="metric name for evaluation")
    cache: Dict[str, Any] = Field(default={}, description="cache for evaluation")
    eval_prompt: Prompt = Field(
        default=Prompt(
            template="""你需要扮演一个裁判的角色，对一段角色扮演的对话内容进行打分，你需要考虑这段文本中的角色沉浸度和对话文本的通畅程度。你可以根据以下规则来进行打分，你可以阐述你对打分标准的理解后再给出分数：
"4":完全可以扮演提问中的角色进行对话，回答完全符合角色口吻和身份，文本流畅语句通顺
"3":扮演了提问中正确的角色，回答完全符合角色口吻和身份，但文本不流畅或字数不满足要求
"2":扮演了提问中正确的角色，但是部分语句不符合角色口吻和身份，文本流畅语句通顺
"1":能够以角色的口吻和身份进行一部分对话，和角色设定有一定偏差，回答内容不流畅，或不满足文本字数要求
"0":扮演了错误的角色，没有扮演正确的角色，角色设定和提问设定差异极大，完全不满意
你的回答需要以json代码格式输出：
```json
{"modelA": {"justification": "此处阐述对打分标准的理解", "score": "此处填写打分结果"}}
```

现在你可以开始回答了：
问题：{{input}}
---
modelA回答：{{output}}
---""",
            identifier="{{}}",
        ),
        description="evaluation prompt",
    )

    class Config:
        arbitrary_types_allowed = True

    def evaluate(
        self, input: Union[str, List[Dict[str, Any]]], reference: str, output: str
    ) -> Dict[str, Any]:
        """
        使用模型进行本地评估
        :param input: 给定的prompt，
            evaluateManager.eval()的is_chat参数为true时,
            input为对话记录，否则为单字符串prompt
        :param reference: 用户给定的标准答案
        :param output: 大模型生成的结果，eval中由service生成，eval_only中由用户给定

        :return: 评估结果
        """

        score = 0
        model_output = None
        try:
            p, _ = self.eval_prompt.render(
                **{
                    "input": "\n".join([i["content"] for i in input]) if not isinstance(input, str) else input,
                    "output": output,
                    "expect": reference,
                }
            )
            if p in self.cache:
                model_output = self.cache[p]
                score = float(model_output["modelA"]["score"])
            else:
                r = self.model.do(
                    messages=[{"role": "user", "content": p}], temperature=0.01
                )
                content = r["result"]
                model_output = content
                regex = re.compile("\`\`\`json(.*)\`\`\`", re.MULTILINE | re.DOTALL)

                u = regex.findall(content)

                # print(u)
                if len(u) == 0:
                    score = 0
                else:
                    model_output = json.loads(u[0])
                    score = float(model_output["modelA"]["score"])
                    self.cache[p] = model_output
        except Exception as e:
            raise e
            score = 0
        return {self.metric_name: score, "eval_output": model_output}

    def summarize(self, metric_dataset: Dataset) -> Optional[Dict[str, Any]]:
        statistics_dict: Dict[str, Any] = {}
        count_dict: Dict[str, int] = {}

        for line in metric_dataset.list():
            for k, v in line.items():
                if isinstance(v, bool):
                    if f"{k}占比" not in statistics_dict:
                        statistics_dict[f"{k}占比"] = 0
                        count_dict[f"{k}占比"] = 0

                    statistics_dict[f"{k}占比"] += 1 if v else 0
                    count_dict[f"{k}占比"] += 1

                elif isinstance(v, (int, float)):
                    if f"{k}平均值" not in statistics_dict:
                        statistics_dict[f"{k}平均值"] = 0
                        count_dict[f"{k}平均值"] = 0

                    if v != -1 and v != -1.0:
                        statistics_dict[f"{k}平均值"] += v
                        count_dict[f"{k}平均值"] += 1
        for k, v in statistics_dict.items():
            if count_dict.get(k, 0):
                statistics_dict[k] = v / count_dict[k]
            else:
                statistics_dict[k] = "不存在可计算值"
        return statistics_dict
