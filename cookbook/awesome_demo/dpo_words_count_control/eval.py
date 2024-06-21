from qianfan.model import Model
from qianfan.common import Prompt
from qianfan import Completion
import re
from qianfan.dataset import Dataset

def eval(version_id, ds):
    result_ds = ds.test_using_llm(model_version_id=version_id)
    res = []
    for i in result_ds:
        
        # 提取字数限制
        char_limit_match = re.search(r"(\d+)字", i['prompt'])
        if not char_limit_match:
            raise ValueError("输入中未找到字数限制")
        
        limit = int(char_limit_match.group(1))
        fact = len(i['llm_output'])

        # 计算比例
        ratio = fact / limit
        abs_diff = abs(ratio - 1)

        # 根据绝对值的大小返回相应的得分
        if abs_diff <= 0.05:
            score = 1
        elif abs_diff <= 0.10:
            score = 0.75
        elif abs_diff <= 0.15:
            score = 0.5
        elif abs_diff <= 0.20:
            score = 0.25
        elif abs_diff <= 0.25:
            score = 0.1
        else:
            score = 0
        res.append(score)
    avg = sum(res) / len(res)
    return avg