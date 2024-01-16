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

import emoji

# 字符重复率算子使用

_character_repetition_length_map = {
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

_character_repetition_max_cutoff_map = {
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

_special_character_map = {
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

default_special_characters_set = set(main_special_characters + other_special_characters)

default_special_characters_set.update(emoji_en)
