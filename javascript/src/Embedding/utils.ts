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
 * 对话请求公共服务模型列表
 */
export type EmbeddingModel =
    | 'Embedding-V1'
    | 'bge-large-en'
    | 'bge-large-zh'
    | 'tao-8k'

export const modelInfoMap: QfLLMInfoMap = {
    'Embedding-V1': {
        endpoint: '/embeddings/embedding-v1',
        required_keys: ['input'],
        optional_keys: ['user_id'],
    },
    'bge-large-en': {
        endpoint: '/embeddings/bge_large_en',
        required_keys: ['input'],
        optional_keys: ['user_id'],
    },
    'bge-large-zh': {
        endpoint: '/embeddings/bge_large_zh',
        required_keys: ['input'],
        optional_keys: ['user_id'],
    },
    'tao-8k': {
        endpoint: '/embeddings/tao_8k',
        required_keys: ['input'],
        optional_keys: ['user_id'],
    },
    UNSPECIFIED_MODEL: {
        endpoint: '',
        required_keys: ['input'],
        optional_keys: [],
    },
};