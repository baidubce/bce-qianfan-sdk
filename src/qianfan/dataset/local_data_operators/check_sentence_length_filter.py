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
data operator for local using
"""

from typing import Any, Dict, Optional

from qianfan.dataset.local_data_operators.base_local_data_operator import (
    BaseLocalFilterOperator,
)
from qianfan.dataset.local_data_operators.local_operator_utils import (
    pyltp_split_sentence,
)
from qianfan.utils.pydantic import Field, root_validator


class LocalCheckEachSentenceIsLongEnoughFilter(BaseLocalFilterOperator):
    """check sentence length"""

    short_sentence_ratio_max_cutoff: Optional[int] = Field(default=None)
    short_sentence_max_cutoff: Optional[int] = Field(default=None)

    @root_validator
    @classmethod
    def _fill_param(cls, input_dicts: Dict[str, Any]) -> Dict[str, Any]:
        if not input_dicts["short_sentence_ratio_max_cutoff"]:
            input_dicts["short_sentence_ratio_max_cutoff"] = 0.6

        if not input_dicts["short_sentence_max_cutoff"]:
            input_dicts["short_sentence_max_cutoff"] = 5

        return input_dicts

    def __str__(self) -> str:
        s = "filter_name: filter_check_each_sentence_is_long_enough\n"
        kwargs = {
            "text_language": self.text_language,
            "short_sentence_ratio_max_cutoff": self.short_sentence_ratio_max_cutoff,
            "short_sentence_max_cutoff": self.short_sentence_max_cutoff,
        }
        for k, v in kwargs.items():
            s += f"\t\t{k}: {v}\n"
        return s

    def __call__(self, entry: Dict[str, Any], *args: Any, **kwargs: Any) -> bool:
        sentences = pyltp_split_sentence(entry[self.filter_column])
        if len(sentences) == 0:
            return False

        assert self.short_sentence_ratio_max_cutoff
        assert self.short_sentence_max_cutoff

        cond = True
        hit = 0

        for sent in sentences:
            if len(sent) <= self.short_sentence_max_cutoff:
                hit += 1
        short_sentence_ratio = hit / len(sentences)
        if short_sentence_ratio > self.short_sentence_ratio_max_cutoff:
            cond = False

        return cond
