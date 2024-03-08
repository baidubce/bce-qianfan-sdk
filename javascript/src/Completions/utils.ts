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

import {QfLLMInfoMap, CompletionBody} from '../interface';

/**
 * 续写公共服务模型列表
 */
export type CompletionModel =
    | 'ERNIE-Bot-turbo'
    | 'ERNIE-Bot'
    | 'ERNIE-Bot-4'
    | 'ERNIE-Bot-8k'
    | 'ERNIE-Speed'
    | 'EB-turbo-AppBuilder'
    | 'BLOOMZ-7B'
    | 'Llama-2-7b-chat'
    | 'Llama-2-13b-chat'
    | 'Llama-2-70b-chat'
    | 'Qianfan-BLOOMZ-7B-compressed'
    | 'Qianfan-Chinese-Llama-2-7B'
    | 'ChatGLM2-6B-32K'
    | 'AquilaChat-7B'
    | 'XuanYuan-70B-Chat-4bit'
    | 'Qianfan-Chinese-Llama-2-13B'
    | 'ChatLaw'
    | 'SQLCoder-7B'
    | 'CodeLlama-7b-Instruct'
    | 'Yi-34B-Chat';

export const modelInfoMap: QfLLMInfoMap = {
    'ERNIE-Bot-turbo': {
        endpoint: '/chat/eb-instant',
        required_keys: ['messages'],
        optional_keys: [
            'stream',
            'temperature',
            'top_p',
            'penalty_score',
            'user_id',
            'tools',
            'tool_choice',
            'system',
        ],
    },
    'ERNIE-Bot': {
        endpoint: '/chat/completions',
        required_keys: ['messages'],
        optional_keys: [
            'stream',
            'temperature',
            'top_p',
            'penalty_score',
            'user_id',
            'system',
            'stop',
            'disable_search',
            'enable_citation',
            'max_output_tokens',
        ],
    },
    'ERNIE-Bot-4': {
        endpoint: '/chat/completions_pro',
        required_keys: ['messages'],
        optional_keys: [
            'stream',
            'temperature',
            'top_p',
            'penalty_score',
            'user_id',
            'system',
            'stop',
            'disable_search',
            'enable_citation',
            'max_output_tokens',
        ],
    },
    'ERNIE-Bot-8k': {
        endpoint: '/chat/ernie_bot_8k',
        required_keys: ['messages'],
        optional_keys: [
            'functions',
            'temperature',
            'top_p',
            'penalty_score',
            'stream',
            'system',
            'stop',
            'disable_search',
            'enable_citation',
            'user_id',
        ],
    },
    'ERNIE-Speed': {
        endpoint: '/chat/eb_turbo_pro',
        required_keys: ['messages'],
        optional_keys: [
            'stream',
            'temperature',
            'top_p',
            'penalty_score',
            'user_id',
            'tools',
            'tool_choice',
            'system',
        ],
    },
    'EB-turbo-AppBuilder': {
        endpoint: '/chat/ai_apaas',
        required_keys: ['messages'],
        optional_keys: [
            'stream',
            'temperature',
            'top_p',
            'penalty_score',
            'system',
            'user_id',
            'tools',
            'tool_choice',
        ],
    },
    'BLOOMZ-7B': {
        endpoint: '/chat/bloomz_7b1',
        required_keys: ['messages'],
        optional_keys: [
            'stream',
            'user_id',
            'temperature',
            'top_k',
            'top_p',
            'penalty_score',
            'stop',
            'tools',
            'tool_choice',
        ],
    },
    'Llama-2-7b-chat': {
        endpoint: '/chat/llama_2_7b',
        required_keys: ['messages'],
        optional_keys: [
            'stream',
            'user_id',
            'temperature',
            'top_k',
            'top_p',
            'penalty_score',
            'stop',
            'tools',
            'tool_choice',
        ],
    },
    'Llama-2-13b-chat': {
        endpoint: '/chat/llama_2_13b',
        required_keys: ['messages'],
        optional_keys: [
            'stream',
            'user_id',
            'temperature',
            'top_k',
            'top_p',
            'penalty_score',
            'stop',
            'tools',
            'tool_choice',
        ],
    },
    'Llama-2-70b-chat': {
        endpoint: '/chat/llama_2_70b',
        required_keys: ['messages'],
        optional_keys: [
            'stream',
            'user_id',
            'temperature',
            'top_k',
            'top_p',
            'penalty_score',
            'stop',
            'tools',
            'tool_choice',
        ],
    },
    'Qianfan-BLOOMZ-7B-compressed': {
        endpoint: '/chat/qianfan_bloomz_7b_compressed',
        required_keys: ['messages'],
        optional_keys: [
            'stream',
            'user_id',
            'temperature',
            'top_k',
            'top_p',
            'penalty_score',
            'stop',
            'tools',
            'tool_choice',
        ],
    },
    'Qianfan-Chinese-Llama-2-7B': {
        endpoint: '/chat/qianfan_chinese_llama_2_7b',
        required_keys: ['messages'],
        optional_keys: [
            'stream',
            'user_id',
            'temperature',
            'top_k',
            'top_p',
            'penalty_score',
            'stop',
            'tools',
            'tool_choice',
        ],
    },
    'ChatGLM2-6B-32K': {
        endpoint: '/chat/chatglm2_6b_32k',
        required_keys: ['messages'],
        optional_keys: [
            'stream',
            'user_id',
            'temperature',
            'top_k',
            'top_p',
            'penalty_score',
            'stop',
            'tools',
            'tool_choice',
        ],
    },
    'AquilaChat-7B': {
        endpoint: '/chat/aquilachat_7b',
        required_keys: ['messages'],
        optional_keys: [
            'stream',
            'user_id',
            'temperature',
            'top_k',
            'top_p',
            'penalty_score',
            'stop',
            'tools',
            'tool_choice',
        ],
    },
    'XuanYuan-70B-Chat-4bit': {
        endpoint: '/chat/xuanyuan_70b_chat',
        required_keys: ['messages'],
        optional_keys: [
            'stream',
            'user_id',
            'temperature',
            'top_k',
            'top_p',
            'penalty_score',
            'stop',
            'tools',
            'tool_choice',
        ],
    },
    'Qianfan-Chinese-Llama-2-13B': {
        endpoint: '/chat/qianfan_chinese_llama_2_13b',
        required_keys: ['messages'],
        optional_keys: [
            'stream',
            'user_id',
            'temperature',
            'top_k',
            'top_p',
            'penalty_score',
            'stop',
            'tools',
            'tool_choice',
        ],
    },
    'ChatLaw': {
        endpoint: '/chat/chatlaw',
        required_keys: ['messages', 'extra_parameters'],
        optional_keys: [
            'stream',
            'user_id',
            'temperature',
            'top_p',
            'tools',
            'tool_choice',
        ],
    },
    'SQLCoder-7B': {
        endpoint: '/completions/sqlcoder_7b',
        required_keys: ['prompt'],
        optional_keys: [
            'stream',
            'user_id',
            'temperature',
            'top_k',
            'top_p',
            'penalty_score',
            'stop',
            'tools',
            'tool_choice',
        ],
    },
    'CodeLlama-7b-Instruct': {
        endpoint: '/completions/codellama_7b_instruct',
        required_keys: ['prompt'],
        optional_keys: [
            'stream',
            'user_id',
            'temperature',
            'top_k',
            'top_p',
            'penalty_score',
            'stop',
            'tools',
            'tool_choice',
        ],
    },
    'Yi-34B-Chat': {
        endpoint: '/chat/yi_34b_chat',
        required_keys: ['messages'],
        optional_keys: [
            'stream',
            'user_id',
            'temperature',
            'top_k',
            'top_p',
            'penalty_score',
            'stop',
            'tools',
            'tool_choice',
        ],
    },
    UNSPECIFIED_MODEL: {
        endpoint: '',
        required_keys: ['prompt'],
        optional_keys: [],
    },
};

// 检查是否为CompletionBody
export function isCompletionBody(body: any): body is CompletionBody {
    return 'prompt' in body;
}