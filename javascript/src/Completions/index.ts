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
import {ChatBody, CompletionBody, Resp} from '../interface';
import {modelInfoMap, isCompletionBody} from './utils';
import {getPathAndBody, getUpperCaseModelAndModelMap} from '../utils';
import {getTypeMap, typeModelEndpointMap} from '../DynamicModelEndpoint/utils';
import {ModelType} from '../enum';

class Completions extends BaseClient {
    /**
     * 续写
     * @param body 续写请求体
     * @param model 续写模型，默认为 'ERNIE-Bot-turbo'
     * @returns 返回 Promise 对象，异步获取续写结果
     */
    public async completions(
        body: CompletionBody,
        model = 'ERNIE-Bot-turbo'
    ): Promise<Resp | AsyncIterable<Resp>> {
        const stream = body.stream ?? false;
        const {modelInfoMapUppercase, modelUppercase} = getUpperCaseModelAndModelMap(model, modelInfoMap);
        // 兼容Chat模型
        const required_keys = modelInfoMapUppercase[modelUppercase]?.required_keys;
        let reqBody: CompletionBody | ChatBody;
        const type = ModelType.COMPLETIONS;
        if (required_keys.includes('messages') && isCompletionBody(body)) {
            const {prompt, ...restOfBody} = body;
            reqBody = {
                ...restOfBody, // 保留除prompt之外的所有属性
                messages: [
                    {
                        role: 'user',
                        content: prompt,
                    },
                ],
            };
        }
        else {
            reqBody = body;
        }
        const modelKey = model.toLowerCase();
        const typeMap = getTypeMap(typeModelEndpointMap, type) ?? new Map();
        const endPoint = typeMap.get(modelKey) || '';
        const {AKPath, requestBody} = getPathAndBody({
            model: modelUppercase,
            modelInfoMap: modelInfoMapUppercase,
            baseUrl: this.qianfanBaseUrl,
            body: reqBody,
            endpoint: this.Endpoint ?? endPoint,
            type,
        });
        return this.sendRequest(type, model, AKPath, requestBody, stream);
    }
}

export default Completions;
