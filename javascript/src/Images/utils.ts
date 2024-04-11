// Copyright (c) 2024 Baidu, Inc. All Rights Reserved.
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//     http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

import {QfLLMInfoMap} from '../interface';

/**
 * 文生图模型
 */
export type Text2ImageModel =
    | 'Stable-Diffusion-XL';

export const text2ImageModelInfoMap: QfLLMInfoMap = {
    'Stable-Diffusion-XL': {
        endpoint: '/text2image/sd_xl',
        required_keys: ['prompt'],
        optional_keys: [
            'negative_prompt',
            'size',
            'n',
            'steps',
            'sampler_index',
            'user_id',
            'seed',
            'cfg_scale',
            'style',
        ],
    },
    UNSPECIFIED_MODEL: {
        endpoint: '',
        required_keys: ['prompt'],
        optional_keys: [],
    },
};

export const image2TextModelInfoMap: QfLLMInfoMap = {
    'Fuyu-8B': {
        endpoint: '/image2text/fuyu_8b',
        required_keys: ['prompt'],
        optional_keys: [
            'image',
            'stream',
            'temperature',
            'top_k',
            'user_id',
            'top_p',
            'penalty_score',
            'stop',
        ],
    },
    UNSPECIFIED_MODEL: {
        endpoint: '',
        required_keys: ['prompt'],
        optional_keys: [],
    },
};
