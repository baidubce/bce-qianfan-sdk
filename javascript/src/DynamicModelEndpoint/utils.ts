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

import {ModelType} from '../enum';

type ModelEndpointMap = Map<string, Map<string, string>>;
const typeModelEndpointMap: ModelEndpointMap = new Map();

// 定义 "CHAT" 类型的模型及其 endpoints
const chatModelEndpoints = new Map<string, string>([
    // ERNIE 4.0
    ['ernie-4.0-8k', 'completions_pro'],
    ['ernie-4.0-8k-preview', 'ernie-4.0-8k-preview'],
    ['ernie-4.0-8k-latest', 'ernie-4.0-8k-latest'],
    ['ernie-4.0-8k-0329', 'ernie-4.0-8k-0329'],
    ['ernie-4.0-8k-0613', 'ernie-4.0-8k-0613'],
    // ERNIE 4.0 Turbo
    ['ernie-4.0-turbo-8k', 'ernie-4.0-turbo-8k'],
    ['ernie-4.0-turbo-8k-preview', 'ernie-4.0-turbo-8k-preview'],
    // ERNIE 3.5
    ['ernie-3.5-8k', 'completions'],
    ['ernie-3.5-8k-preview', 'ernie-3.5-8k-preview'],
    ['ernie-3.5-8k-0329', 'ernie-3.5-8k-0329'],
    ['ernie-3.5-128k', 'ernie-3.5-128k'],
    ['ernie-3.5-8k-0613', 'ernie-3.5-8k-0613'],
    ['ernie-3.5-8k-0701', 'ernie-3.5-8k-0701'],
    // ERNIE Speed Pro
    ['ernie-speed-pro-8k', 'ernie-speed-pro-8k'],
    ['ernie-speed-pro-128k', 'ernie-speed-pro-128k'],
    // ERNIE Speed
    ['ernie-speed-8k', 'ernie_speed'],
    ['ernie-speed-128k', 'ernie-speed-128k'],
    // ERNIE Lite Pro
    ['ernie-lite-pro-8k', 'ernie-lite-pro-8k'],
    // ERNIE Lite
    ['ernie-lite-8k-0922', 'eb-instant'],
    ['ernie-lite-8k', 'ernie-lite-8k'],
    ['ernie-lite-8k-0725', 'ernie-lite-8k-0725'],
    ['ernie-lite-4k-0704', 'ernie-lite-4k-0704'],
    ['ernie-lite-4k-0516', 'ernie-lite-4k-0516'],
    ['ernie-lite-128k-0419', 'ernie-lite-128k-0419'],
    ['ernie-lite-8k-0308', 'ernie-lite-8k'],

    ['ernie-tiny-8k', 'ernie-tiny-8k'],
    ['ernie-novel-8k', 'ernie-novel-8k'],
    ['ernie-character-8k', 'ernie-char-8k'],
    ['ernie-functions-8k', 'ernie-func-8k'],
    ['qianfan-dynamic-8k', 'qianfan-dynamic-8k'],

    // ERNIE AppBuilder
    ['ernie-speed-appbuilder', 'ai_apaas'],

    ['ernie-4.0-8k-preemptible', 'completions_pro_preemptible'],
    ['ernie-4.0-8k-0104', 'ernie-4.0-8k-0104'],
    ['ernie-3.5-8k-0205', 'ernie-3.5-8k-0205'],
    ['ernie-3.5-8k-1222', 'ernie-3.5-8k-1222'],
    ['ernie-3.5-4k-0205', 'ernie-3.5-4k-0205'],
    ['ernie-3.5-8k-preemptible', 'completions_preemptible'],

    ['ernie-character-8k-0321', 'ernie-char-8k'],

    ['gemma-7b-it', 'gemma_7b_it'],
    ['yi-34b-chat', 'yi_34b_chat'],
    ['bloomz-7b', 'bloomz_7b1'],
    ['qianfan-bloomz-7b-compressed', 'qianfan_bloomz_7b_compressed'],
    ['mixtral-8x7b-instruct', 'mixtral_8x7b_instruct'],
    ['llama-2-7b-chat', 'llama_2_7b'],
    ['llama-2-13b-chat', 'llama_2_13b'],
    ['llama-2-70b-chat', 'llama_2_70b'],
    ['meta-llama-3-8b-instruct', 'llama_3_8b'],
    ['meta-llama-3-70b-instruct', 'llama_3_70b'],
    ['qianfan-chinese-llama-2-7b', 'qianfan_chinese_llama_2_7b'],
    ['qianfan-chinese-llama-2-13b-v1', 'qianfan_chinese_llama_2_13b'],
    ['qianfan-chinese-llama-2-70b', 'qianfan_chinese_llama_2_70b'],
    ['chatglm2-6b-32k', 'chatglm2_6b_32k'],
    ['xuanyuan-70b-chat-4bit', 'xuanyuan_70b_chat'],
    ['chatlaw', 'chatlaw'],
    ['aquilachat-7b', 'aquilachat_7b'],
    // Compatibility for old model names
    // ['ernie-bot-turbo', 'eb-instant'],
    ['ernie-bot', 'completions'],
    ['ernie-bot-4', 'completions_pro'],
    ['ernie-bot-8k', 'ernie_bot_8k'],
    ['ernie-speed', 'ernie_speed'],
    ['ernie-bot-turbo-ai', 'ai_apaas'],
    ['eb-turbo-appbuilder', 'ai_apaas'],
    ['qianfan-chinese-llama-2-13b', 'qianfan_chinese_llama_2_13b'],

    ['ernie-lite-appbuilder-8k-0614', 'ai_apaas_lite'],
    ['ernie-character-fiction-8k', 'ernie-char-fiction-8k']
]);
// 定义 "COMPLETIONS" 类型的模型及其 endpoints
const completionsModelEndpoints = new Map<string, string>([
    ['sqlcoder-7b', 'sqlcoder_7b'],
    ['codellama-7b-instruct', 'codellama_7b_instruct']
]);

// 定义 "EMBEDDINGS" 类型的模型及其 endpoints
const embeddingEndpoints = new Map<string, string>([
    ['embedding-v1', 'embedding-v1'],
    ['bge-large-zh', 'bge_large_zh'],
    ['bge-large-en', 'bge_large_en'],
    ['tao-8k', 'tao_8k']
]);

// 定义 "TEXT_2_IMAGE" 类型的模型及其 endpoints
const text2imageEndpoints = new Map<string, string>([['stable-diffusion-xl', 'sd_xl']]);

// 定义 "IMAGE_2_TEXT" 类型的模型及其 endpoints
const image2textEndpoints = new Map<string, string>([['fuyu-8b', 'fuyu_8b']]);

// 一言插件模型
const pluginEndpoints = new Map<string, string>([['ebpluginv2', 'erniebot/plugin']]);

// 重新排序向量模型
const rerankerEndpoints = new Map<string, string>([['bce-reranker-base_v1', 'bce_reranker_base']]);

// 将模型 endpoints 映射添加到主映射中
typeModelEndpointMap.set(ModelType.CHAT, chatModelEndpoints);
typeModelEndpointMap.set(ModelType.COMPLETIONS, completionsModelEndpoints);
typeModelEndpointMap.set(ModelType.EMBEDDINGS, embeddingEndpoints);
typeModelEndpointMap.set(ModelType.TEXT_2_IMAGE, text2imageEndpoints);
typeModelEndpointMap.set(ModelType.IMAGE_2_TEXT, image2textEndpoints);
typeModelEndpointMap.set(ModelType.PLUGIN, pluginEndpoints);
typeModelEndpointMap.set(ModelType.RERANKER, rerankerEndpoints);

export {typeModelEndpointMap};
// 检查CHAT是否有数据的函数
export function getTypeMap(typeMap: ModelEndpointMap, type): Map<string, string> | undefined {
    const chatMap = typeMap.get(type);
    if (chatMap && chatMap.size > 0) {
        return chatMap; // 返回CHAT对应的映射
    }
    return undefined;
}
