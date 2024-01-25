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
constants of local data operator
"""
import string
from typing import Dict, List, Set

import emoji

# 字符重复率算子使用

_character_repetition_length_map: Dict[str, int] = {
    "AR": 10,
    "BN": 10,
    "CA": 10,
    "EN": 10,
    "ES": 10,
    "EU": 10,
    "FR": 10,
    "HI": 10,
    "ID": 10,
    "PT": 10,
    "UR": 10,
    "VI": 10,
    "ZH": 3,
}

_character_repetition_max_cutoff_map: Dict[str, float] = {
    "AR": 0.20,
    "BN": 0.13,
    "CA": 0.20,
    "EN": 0.106,
    "ES": 0.14,
    "EU": 0.20,
    "FR": 0.14,
    "HI": 0.18,
    "ID": 0.15,
    "PT": 0.25,
    "UR": 0.19,
    "VI": 0.15,
    "ZH": 0.2,
}

# 检查特殊词比例算子使用

_special_character_map: Dict[str, float] = {
    "AR": 0.30,
    "BN": 0.45,
    "CA": 0.25,
    "EN": 0.40,
    "ES": 0.34,
    "EU": 0.31,
    "FR": 0.34,
    "HI": 0.45,
    "ID": 0.34,
    "PT": 0.35,
    "UR": 0.25,
    "VI": 0.34,
    "ZH": 0.30,
}

main_special_characters = string.punctuation + string.digits + string.whitespace

other_special_characters = (
    "    　    ￼’“”–ー一▬…✦�­£​•€«»°·═"
    "×士＾˘⇓↓↑←→（）§″′´¿−±∈﻿¢ø‚„½¼¾¹²³―⁃，ˌ¸‹›ʺˈʻ¦‐⠀‰‑≤≥‖"
    "◆●■►▼▲▴∆▻¡★☆✱ːº。¯˜¥ɪ≈†上ン：∼⁄・♡✓⊕․．⋅÷１‟；،、¨ाাी्े◦˚"
    "゜ʼ≖ʼ¤ッツシ℃√！【】‿∞➤～πه۩☛₨➩☻๑٪♥ıॽ《‘©﴿٬？▷Г♫∟™ª₪®「—❖"
    "」﴾》"
)

# emoji 表情列表
emoji_en = list(emoji.EMOJI_DATA.keys())

_default_special_characters_set: Set[str] = set(
    main_special_characters + other_special_characters
)

_default_special_characters_set.update(emoji_en)

# 敏感词过滤算子使用

_words_augmentation_group_sizes_map: Dict[str, List[int]] = {
    "AR": [],
    "BN": [],
    "CA": [],
    "EN": [],
    "ES": [],
    "EU": [],
    "FR": [],
    "HI": [],
    "ID": [],
    "PT": [],
    "UR": [],
    "VI": [2],
    "ZH": [2],
}

_words_augmentation_join_char_map: Dict[str, str] = {
    "AR": "",
    "BN": "",
    "CA": "",
    "EN": "",
    "ES": "",
    "EU": "",
    "FR": "",
    "HI": "",
    "ID": "",
    "PT": "",
    "UR": "",
    "VI": " ",
    "ZH": "",
}

_flagged_words_max_cutoff_map: Dict[str, float] = {
    "AR": 0.03,
    "BN": 0.001,
    "CA": 0.1,
    "EN": 0.01,
    "ES": 0.01,
    "EU": 0.1,
    "FR": 0.008,
    "HI": 0.005,
    "ID": 0.01,
    "PT": 0.007,
    "UR": 0.025,
    "VI": 0.005,
    "ZH": 0.001,
}

# 词数检查算子使用

_number_words_min_map: Dict[str, int] = {
    "AR": 20,
    "BN": 33,
    "CA": 15,
    "EN": 20,
    "ES": 16,
    "EU": 8,
    "FR": 13,
    "HI": 38,
    "ID": 15,
    "PT": 19,
    "UR": 25,
    "VI": 30,
    "ZH": 1,
}

_number_words_max_map: Dict[str, int] = {
    "AR": 100000,
    "BN": 100000,
    "CA": 100000,
    "EN": 100000,
    "ES": 100000,
    "EU": 100000,
    "FR": 100000,
    "HI": 100000,
    "ID": 100000,
    "PT": 100000,
    "UR": 100000,
    "VI": 100000,
    "ZH": 1000000,
}

# 停止词检查算子使用

_stopwords_min_cutoff_map = {
    "AR": 0.07,
    "BN": 0.002,
    "CA": 0.25,
    "EN": 0.30,
    "ES": 0.4,
    "EU": 0.05,
    "FR": 0.27,
    "HI": 0.01,
    "ID": 0.15,
    "PT": 0.20,
    "UR": 0.01,
    "VI": 0.08,
    "ZH": 0.1691,
}

# 词重复检查算子使用

_word_repetition_length_map = {
    "AR": 5,
    "BN": 5,
    "CA": 5,
    "EN": 5,
    "ES": 5,
    "EU": 5,
    "FR": 5,
    "HI": 5,
    "ID": 5,
    "PT": 5,
    "UR": 7,
    "VI": 5,
    "ZH": 5,
}

_word_repetition_max_cutoff = {
    "AR": 0.34,
    "BN": 0.21,
    "CA": 0.40,
    "EN": 0.19,
    "ES": 0.25,
    "EU": 0.40,
    "FR": 0.13,
    "HI": 0.47,
    "ID": 0.20,
    "PT": 0.98,
    "UR": 0.50,
    "VI": 0.20,
    "ZH": 0.96,
}
