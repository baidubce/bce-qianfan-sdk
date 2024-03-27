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
 * 一言插件 v2
 */
export type Image2TextModel =
    | 'EBPluginV2';

export const modelInfoMap: QfLLMInfoMap = {
    'EBPluginV2': {
        endpoint: '/erniebot/plugin',
        required_keys: ['messages', 'plugins'],
        optional_keys: [
            'user_id',
            'extra_data',
        ],
    },
    UNSPECIFIED_MODEL: {
        endpoint: '',
        required_keys: ['query'],
        optional_keys: [],
    },
};