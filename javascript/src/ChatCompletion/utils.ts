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
export type ChatModel =
    | 'ERNIE-4.0-8K-Latest'
    | 'ERNIE-4.0-8K-0613'
    | 'ERNIE-3.5-8K-0613'
    | 'ERNIE-4.0-8K'
    | 'ERNIE-3.5-8K'
    | 'ERNIE-3.5-8K-0205'
    | 'ERNIE-3.5-8K-1222'
    | 'ERNIE-3.5-4K-0205'
    | 'ERNIE-Speed-128K'
    | 'ERNIE-Lite-8K-0922'
    | 'ERNIE-Lite-8K-0308'
    | 'ERNIE Speed-AppBuilder'
    | 'Gemma-7B-it'
    | 'Mixtral-8x7B-Instruct'
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
    'ERNIE-4.0-8K-Latest': {
        endpoint: '/chat/ernie-4.0-8k-latest',
        required_keys: ['messages'],
        optional_keys: [
            'stream',
            'temperature',
            'top_p',
            'penalty_score',
            'user_id',
            'system',
            'stop',
            'enable_system_memory',
            'system_memory_id',
            'disable_search',
            'enable_citation',
            'enable_trace',
            'max_output_tokens',
            'response_format',
        ],
    },
    'ERNIE-4.0-8K-0613': {
        endpoint: '/chat/ernie-4.0-8k-0613',
        required_keys: ['messages'],
        optional_keys: [
            'stream',
            'temperature',
            'top_p',
            'penalty_score',
            'user_id',
            'system',
            'stop',
            'enable_system_memory',
            'system_memory_id',
            'disable_search',
            'enable_citation',
            'enable_trace',
            'max_output_tokens',
            'response_format',
        ],
    },
    'ERNIE-3.5-8K-0613': {
        endpoint: '/chat/ernie-3.5-8k-0613',
        required_keys: ['messages'],
        optional_keys: [
            'stream',
            'temperature',
            'top_p',
            'penalty_score',
            'user_id',
            'system',
            'stop',
            'enable_system_memory',
            'system_memory_id',
            'disable_search',
            'enable_citation',
            'enable_trace',
            'max_output_tokens',
            'response_format',
            'functions',
            'tool_choice',
        ],
    },
    'ERNIE-4.0-8K': {
        endpoint: '/chat/completions_pro',
        required_keys: ['messages'],
        optional_keys: ['stream', 'temperature', 'top_p', 'penalty_score', 'user_id', 'tools', 'tool_choice', 'system'],
    },
    'ERNIE-3.5-8K': {
        endpoint: '/chat/completions',
        required_keys: ['messages'],
        optional_keys: ['stream', 'temperature', 'top_p', 'penalty_score', 'user_id', 'tools', 'tool_choice', 'system'],
    },
    'ERNIE-3.5-8K-0205': {
        endpoint: '/chat/ERNIE-3.5-8K-0205',
        required_keys: ['messages'],
        optional_keys: ['stream', 'temperature', 'top_p', 'penalty_score', 'user_id', 'tools', 'tool_choice', 'system'],
    },
    'ERNIE-3.5-8K-1222': {
        endpoint: '/chat/ernie-3.5-8k-1222',
        required_keys: ['messages'],
        optional_keys: ['stream', 'temperature', 'top_p', 'penalty_score', 'user_id', 'tools', 'tool_choice', 'system'],
    },
    'ERNIE-3.5-4K-0205': {
        endpoint: '/chat/ernie-3.5-4k-0205',
        required_keys: ['messages'],
        optional_keys: ['stream', 'temperature', 'top_p', 'penalty_score', 'user_id', 'tools', 'tool_choice', 'system'],
    },
    'ERNIE Speed-AppBuilder': {
        endpoint: '/chat/ai_apaas',
        required_keys: ['messages'],
        optional_keys: ['stream', 'temperature', 'top_p', 'penalty_score', 'user_id', 'tools', 'tool_choice', 'system'],
    },
    'Gemma-7B-it': {
        endpoint: '/chat/gemma_7b_it',
        required_keys: ['messages'],
        optional_keys: ['stream', 'temperature', 'top_p', 'penalty_score', 'user_id', 'tools', 'tool_choice', 'system'],
    },
    'ERNIE-Bot-turbo': {
        endpoint: '/chat/eb-instant',
        required_keys: ['messages'],
        optional_keys: ['stream', 'temperature', 'top_p', 'penalty_score', 'user_id', 'tools', 'tool_choice', 'system'],
    },
    'ERNIE-Speed-8K': {
        endpoint: '/chat/ernie_speed',
        required_keys: ['messages'],
        optional_keys: ['stream', 'temperature', 'top_p', 'penalty_score', 'user_id', 'tools', 'tool_choice', 'system'],
    },
    'ERNIE-Speed-128K': {
        endpoint: '/chat/ernie-speed-128k',
        required_keys: ['messages'],
        optional_keys: ['stream', 'temperature', 'top_p', 'penalty_score', 'user_id', 'tools', 'tool_choice', 'system'],
    },
    'ERNIE-Lite-8K-0922': {
        endpoint: '/chat/eb-instant',
        required_keys: ['messages'],
        optional_keys: ['stream', 'temperature', 'top_p', 'penalty_score', 'user_id', 'tools', 'tool_choice', 'system'],
    },
    'ERNIE-Lite-8K-0308': {
        endpoint: '/chat/ernie-lite-8k',
        required_keys: ['messages'],
        optional_keys: ['stream', 'temperature', 'top_p', 'penalty_score', 'user_id', 'tools', 'tool_choice', 'system'],
    },
    'Mixtral-8x7B-Instruct': {
        endpoint: '/chat/mixtral_8x7b_instruct',
        required_keys: ['messages'],
        optional_keys: ['stream', 'temperature', 'top_p', 'penalty_score', 'user_id', 'tools', 'tool_choice', 'system'],
    },
    'ERNIE-Bot': {
        endpoint: '/chat/completions',
        required_keys: ['messages'],
        optional_keys: [
            'stream',
            'temperature',
            'top_p',
            'penalty_score',
            'functions',
            'system',
            'user_id',
            'user_setting',
            'stop',
            'disable_search',
            'enable_citation',
            'max_output_tokens',
            'tool_choice',
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
            'functions',
            'system',
            'user_id',
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
        optional_keys: ['stream', 'temperature', 'top_p', 'penalty_score', 'user_id', 'tools', 'tool_choice', 'system'],
    },
    'ERNIE-Bot-turbo-AI': {
        endpoint: '/chat/ai_apaas',
        required_keys: ['messages'],
        optional_keys: ['stream', 'temperature', 'top_p', 'penalty_score', 'system', 'user_id', 'tools', 'tool_choice'],
    },
    'EB-turbo-AppBuilder': {
        endpoint: '/chat/ai_apaas',
        required_keys: ['messages'],
        optional_keys: ['stream', 'temperature', 'top_p', 'penalty_score', 'system', 'user_id', 'tools', 'tool_choice'],
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
        optional_keys: ['stream', 'user_id', 'temperature', 'top_p', 'tools', 'tool_choice'],
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
    'ernie-lite-8k': {
        endpoint: '/chat/ernie-lite-8k',
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
    'ernie-3.5-128k': {
        endpoint: '/chat/ernie-3.5-128k',
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
    'ernie-character-fiction-8k': {
        endpoint: '/chat/ernie-char-fiction-8k',
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
    'ernie-lite-appbuilder-8k-0614': {
        endpoint: '/chat/ai_apaas_lite',
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
    'ernie-4.0-turbo-8k': {
        endpoint: '/chat/ernie-4.0-turbo-8k',
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
    'qianfan-chinese-llama-2-13b': {
        endpoint: '/chat/qianfan-chinese-llama-2-13b',
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
    'eb-turbo-appbuilder': {
        endpoint: '/chat/ai_apaas',
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
    'ernie-bot-turbo-ai': {
        endpoint: '/chat/ai_apaas',
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
    'ernie-speed': {
        endpoint: '/chat/ernie-speed',
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
    'ernie-bot-8k': {
        endpoint: '/chat/ernie_bot_8k',
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
    'ernie-bot-4': {
        endpoint: '/chat/completions_pro',
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
    'ernie-bot': {
        endpoint: '/chat/completions',
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
    'aquilachat-7b': {
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
    'xuanyuan-70b-chat-4bit': {
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
    'chatglm2-6b-32k': {
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
    'qianfan-chinese-llama-2-70b': {
        endpoint: '/chat/qianfan_chinese_llama_2_70b',
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
    'qianfan-chinese-llama-2-13b-v1': {
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
    'qianfan-chinese-llama-2-7b': {
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
    UNSPECIFIED_MODEL: {
        endpoint: '',
        required_keys: ['messages'],
        optional_keys: [],
    },
};
