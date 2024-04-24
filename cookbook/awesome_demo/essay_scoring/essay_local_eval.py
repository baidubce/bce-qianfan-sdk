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
        x = re.findall('\d+', str_score)
        return int(x[0])
    except:
        return 0
    
embedding = Embedding(query_per_second=5)
    
@cached(cache={})
def get_qianfan_embedding(content: str) -> np.array:
    return np.array(embedding.do([content]).body["data"][0]["embedding"])

def get_cosine_similarity(content1: str, content2: str) -> float:
    vec1 = get_qianfan_embedding(content1)
    vec2 = get_qianfan_embedding(content2)

    return vec1.dot(vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))

class EssayEvaluator(LocalEvaluator):

    def evaluate(self, input: Union[str, List[Dict[str, Any]]], reference: str, output: str) -> Dict[str, Any]:
        try:
            try:
                judge_result: Dict[str, Any] = json.loads(output)
            except:
                # 兼容可能的 Markdown 输出
                judge_result: Dict[str, Any] = json.loads(re.search(r"```json\n([\s\S]*)\n```", output).group(1))

            reference_result: Dict[str, Any] = json.loads(reference)
            return {
                "遵守格式": True,

                "总分之和计算正确": _convert_str_to_int(judge_result["最终得分"]) == 
                                    _convert_str_to_int(judge_result["详细解析"]["内容项"]["得分"]) +
                                    _convert_str_to_int(judge_result["详细解析"]["表达项"]["得分"]) +
                                    _convert_str_to_int(judge_result["详细解析"]["发展等级"]["得分"]) -
                                    _convert_str_to_int(judge_result["详细解析"]["扣分项和残篇评定"]["扣分"]),

                "内容评分等级一致": judge_result["详细解析"]["内容项"]["等级"] ==
                                    reference_result["详细解析"]["内容项"]["等级"],
                "内容点评相似度": get_cosine_similarity(judge_result["详细解析"]["内容项"]["解析"],
                                                        reference_result["详细解析"]["内容项"]["解析"]),
                "内容评分分差": abs(
                    _convert_str_to_int(judge_result["详细解析"]["内容项"]["得分"]) - _convert_str_to_int(
                        reference_result["详细解析"]["内容项"]["得分"])),

                "表达评分等级一致": judge_result["详细解析"]["表达项"]["等级"] ==
                                    reference_result["详细解析"]["表达项"]["等级"],
                "表达点评相似度": get_cosine_similarity(judge_result["详细解析"]["表达项"]["解析"],
                                                        reference_result["详细解析"]["表达项"]["解析"]),
                "表达评分分差": abs(
                    _convert_str_to_int(judge_result["详细解析"]["表达项"]["得分"]) - _convert_str_to_int(
                        reference_result["详细解析"]["表达项"]["得分"])),

                "发展评分等级一致": judge_result["详细解析"]["发展等级"]["等级"] ==
                                    reference_result["详细解析"]["发展等级"]["等级"],
                "发展点评相似度": get_cosine_similarity(judge_result["详细解析"]["发展等级"]["解析"],
                                                        reference_result["详细解析"]["发展等级"]["解析"]),
                "发展评分分差": abs(
                    _convert_str_to_int(judge_result["详细解析"]["发展等级"]["得分"]) - _convert_str_to_int(
                        reference_result["详细解析"]["发展等级"]["得分"])),

                "扣分解析相似度": get_cosine_similarity(judge_result["详细解析"]["扣分项和残篇评定"]["解析"],
                                                        reference_result["详细解析"]["扣分项和残篇评定"]["解析"]),
                "扣分项扣分分差": abs(
                    _convert_str_to_int(judge_result["详细解析"]["扣分项和残篇评定"]["扣分"]) - _convert_str_to_int(
                        reference_result["详细解析"]["扣分项和残篇评定"]["扣分"])),

                "总分分差": abs(
                    _convert_str_to_int(judge_result["最终得分"]) - _convert_str_to_int(reference_result["最终得分"])),
            }
        except:
            return {
                "遵守格式": False,
                "总分之和计算正确": False,
                "内容评分等级一致": False,
                "内容点评相似度": -1,
                "内容评分分差": -1,
                "表达评分等级一致": False,
                "表达点评相似度": -1,
                "表达评分分差": -1,
                "发展评分等级一致": False,
                "发展点评相似度": -1,
                "发展评分分差": -1,
                "扣分解析相似度": -1,
                "扣分项扣分分差": -1,
                "总分分差": -1
            }

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

        flatten_dict: Dict[str, List[int]] = {}

        for line in metric_dataset.list():
            for k, v in line.items():
                if isinstance(v, (int, float)):
                    if k not in flatten_dict:
                        flatten_dict[k] = []

                    flatten_dict[k].append(v)

        import numpy as np
        for k, v in flatten_dict.items():
            statistics_dict[f"{k}方差"] = np.var(v)

        try:
            statistics_dict["质量得分（越小越好）"] = statistics_dict["总分分差平均值"] / statistics_dict["遵守格式占比"]
        except:
            statistics_dict["质量得分（越小越好）"] = "无遵守格式输出"

        return statistics_dict