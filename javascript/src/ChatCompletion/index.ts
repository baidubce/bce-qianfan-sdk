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

import {BaseClient} from '../Base';
import {ChatBody, Resp} from '../interface';
import {getPathAndBody} from '../utils';
import {getTypeMap, typeModelEndpointMap} from '../DynamicModelEndpoint/utils';
import {ModelType} from '../enum';

const type = ModelType.CHAT;
class ChatCompletion extends BaseClient {
    /**
     * chat
     * @param body 聊天请求体
     * @param model 聊天模型，默认为 'ERNIE-Bot-turbo'
     * @param stream 是否开启流模式，默认为 false
     * @returns Promise<ChatResp | AsyncIterable<ChatResp>>
     */
    public async chat(body: ChatBody, model = 'ERNIE-Lite-8K'): Promise<Resp | AsyncIterable<Resp>> {
        const stream = body.stream ?? false;
        const modelKey = model.toLowerCase();
        const typeMap = getTypeMap(typeModelEndpointMap, type) ?? new Map();
        const endPoint = typeMap.get(modelKey) || '';
        const {AKPath, requestBody} = getPathAndBody({
            baseUrl: this.qianfanBaseUrl,
            body,
            endpoint: this.Endpoint ?? endPoint,
            type,
        });
        return this.sendRequest(type, model, AKPath, requestBody, stream);
    }

    public async getModels(): Promise<string[]> {
        return this.getAllModels(type);
    }
}

export default ChatCompletion;
