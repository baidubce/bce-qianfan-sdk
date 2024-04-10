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
    ['ernie-4.0-8k', 'completions_pro'],
    ['ernie-3.5-8k', 'completions'],
    ['ernie-3.5-8k-0205', 'ernie-3.5-8k-0205'],
    ['ernie-3.5-8k-1222', 'ernie-3.5-8k-1222'],
    ['ernie-bot-8k', 'ernie_bot_8k'],
    ['ernie-3.5-4k-0205', 'ernie-3.5-4k-0205'],
    ['ernie-speed-8k', 'ernie_speed'],
    ['ernie-speed-128k', 'ernie-speed-128k'],
    ['ernie-lite-8k-0922', 'eb-instant'],
    ['ernie-lite-8k-0308', 'ernie-lite-8k'],
    ['ernie speed-appbuilder', 'ai_apaas'],
    ['gemma-7b-it', 'gemma_7b_it'],
    ['yi-34b-chat', 'yi_34b_chat'],
    ['bloomz-7b', 'bloomz_7b1'],
    ['qianfan-bloomz-7b-compressed', 'qianfan_bloomz_7b_compressed'],
    ['mixtral-8x7b-instruct', 'mixtral_8x7b_instruct'],
    ['llama-2-7b-chat', 'llama_2_7b'],
    ['llama-2-13b-chat', 'llama_2_13b'],
    ['llama-2-70b-chat', 'llama_2_70b'],
    ['qianfan-chinese-llama-2-7b', 'qianfan_chinese_llama_2_7b'],
    ['qianfan-chinese-llama-2-13b', 'qianfan_chinese_llama_2_13b'],
    ['chatglm2-6b-32k', 'chatglm2_6b_32k'],
    ['xuanyuan-70b-chat-4bit', 'xuanyuan_70b_chat'],
    ['chatlaw', 'chatlaw'],
    ['aquilachat-7b', 'aquilachat_7b'],
    // Compatibility for old model names
    ['ernie-bot-turbo', 'eb-instant'],
    ['ernie-bot', 'completions'],
    ['ernie-bot-4', 'completions_pro'],
    ['ernie-bot-8k', 'ernie_bot_8k'],
    ['ernie-speed', 'ernie_speed'],
    ['ernie-speed-128k', 'ernie_speed'],
    ['ernie-bot-turbo-ai', 'ai_apaas'],
    ['eb-turbo-appbuilder', 'ai_apaas'],
]);
// 定义 "COMPLETIONS" 类型的模型及其 endpoints
const completionsModelEndpoints = new Map<string, string>([
    ['sqlcoder-7b', 'sqlcoder_7b'],
    ['codellama-7b-instruct', 'codellama_7b_instruct'],
]);

// 定义 "EMBEDDINGS" 类型的模型及其 endpoints
const embeddingEndpoints = new Map<string, string>([
    ['embedding-v1', 'embedding-v1'],
    ['bge-large-zh', 'bge_large_zh'],
    ['bge-large-en', 'bge_large_en'],
    ['tao-8k', 'tao_8k'],
]);

// 定义 "TEXT_2_IMAGE" 类型的模型及其 endpoints
const text2imageEndpoints = new Map<string, string>([
    ['stable-diffusion-xl', 'sd_xl'],
]);

// 定义 "IMAGE_2_TEXT" 类型的模型及其 endpoints
const image2textEndpoints = new Map<string, string>([
    ['fuyu-8b', 'fuyu_8b'],
]);

// 将模型 endpoints 映射添加到主映射中
typeModelEndpointMap.set(ModelType.CHAT, chatModelEndpoints);
typeModelEndpointMap.set(ModelType.COMPLETIONS, completionsModelEndpoints);
typeModelEndpointMap.set(ModelType.EMBEDDINGS, embeddingEndpoints);
typeModelEndpointMap.set(ModelType.TEXT_2_IMAGE, text2imageEndpoints);
typeModelEndpointMap.set(ModelType.IMAGE_2_TEXT, image2textEndpoints);

export {typeModelEndpointMap};
// 检查CHAT是否有数据的函数
export function getTypeMap(typeMap: ModelEndpointMap, type): Map<string, string> | undefined {
    const chatMap = typeMap.get(type);
    if (chatMap && chatMap.size > 0) {
        return chatMap; // 返回CHAT对应的映射
    }
    return undefined;
}