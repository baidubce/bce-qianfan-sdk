import json
import re
from typing import Callable, Dict, Any


def exception_capture(func: Callable) -> Callable:
    
    def _wrapper(*args, **kwargs):
        try:
            result = func(*args, **kwargs)
            return result
        except Exception as e:
            return False

    return _wrapper


def _convert_str_to_int(str_score: str) -> int:
    try:
        return int(str_score[:-1])
    except:
        return 0


@exception_capture
def _character_length_filter(entry: Dict[str, Any]) -> bool:
    return len(entry.get("essay", "")) >= 700


@exception_capture
def _character_length_too_long_filter(entry: Dict[str, Any]) -> bool:
    return len(entry.get("essay", "")) <= 400


def character_length_filter_with_cond(is_bad: bool) -> Callable:
    if is_bad:
        return _character_length_too_long_filter
    
    return _character_length_filter


@exception_capture
def low_quality_essay_filter(entry: Dict[str, Any]) -> bool:
    output = entry.get("essay", None)
    if output is None:
        return False

    for word in ["（", "）", "此片", "作文", "文体要求", "文章结构", "偏离题意"]:
        if output.find(word) != -1:
            return False
    return True


@exception_capture
def correction_format_filter(entry: Dict[str, Any]) -> bool:
    output = entry["llm_output"]

    try:
        judge_result: Dict[str, Any] = json.loads(output)
    except:
        # 兼容可能的 Markdown 输出
        try:
            judge_result: Dict[str, Any] = json.loads(re.search(r"```json\n([\s\S]*)\n```", output).group(1))
        except:
            return False

    return True


@exception_capture
def score_consistence_filter(entry: Dict[str, Any]) -> bool:
    output = entry["llm_output"]

    try:
        judge_result: Dict[str, Any] = json.loads(output)
    except:
        # 兼容可能的 Markdown 输出
        judge_result: Dict[str, Any] = json.loads(re.search(r"```json\n([\s\S]*)\n```", output).group(1))

    try:
        if not (
            0 <= _convert_str_to_int(judge_result["最终得分"]) <= 60 and
            0 <= _convert_str_to_int(judge_result["详细解析"]["内容项"]["得分"]) <= 20 and
            0 <= _convert_str_to_int(judge_result["详细解析"]["表达项"]["得分"]) <= 20 and
            0 <= _convert_str_to_int(judge_result["详细解析"]["发展等级"]["得分"]) <= 20 and
            0 <= _convert_str_to_int(judge_result["详细解析"]["扣分项和残篇评定"]["扣分"]) <= 20
        ) or not (
            _convert_str_to_int(judge_result["最终得分"]) ==
            _convert_str_to_int(judge_result["详细解析"]["内容项"]["得分"]) +
            _convert_str_to_int(judge_result["详细解析"]["表达项"]["得分"]) +
            _convert_str_to_int(judge_result["详细解析"]["发展等级"]["得分"]) -
            _convert_str_to_int(judge_result["详细解析"]["扣分项和残篇评定"]["扣分"])
        ):
            return False
    except:
        return False

    return True


@exception_capture
def level_consistence_filter(entry: Dict[str, Any]) -> bool:
    output = entry["llm_output"]

    try:
        judge_result: Dict[str, Any] = json.loads(output)
    except:
        # 兼容可能的 Markdown 输出
        judge_result: Dict[str, Any] = json.loads(re.search(r"```json\n([\s\S]*)\n```", output).group(1))

    level_list = ["一等", "二等", "三等"]

    try:
        if not (
            judge_result["详细解析"]["内容项"]["等级"] in level_list and
            judge_result["详细解析"]["表达项"]["等级"] in level_list and
            judge_result["详细解析"]["发展等级"]["等级"] in level_list
        ):
            return False
    except:
        return False

    return True