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
import {CompletionBody, Resp} from '../interface';
import {modelInfoMap, CompletionModel} from './utils';
import {getPathAndBody} from '../utils';

class Completions extends BaseClient {
    /**
     * 续写
     * @param body 续写请求体
     * @param model 续写模型，默认为 'ERNIE-Bot-turbo'
     * @returns 返回 Promise 对象，异步获取续写结果
     */
    public async completions(
        body: CompletionBody,
        model: CompletionModel = 'ERNIE-Bot-turbo'
    ): Promise<Resp | AsyncIterable<Resp>> {
        const stream = body.stream ?? false;
        const {IAMPath, AKPath, requestBody} = getPathAndBody(model, modelInfoMap, body, this.Endpoint, 'completions');
        return this.sendRequest(IAMPath, AKPath, requestBody, stream);
    }
}

export default Completions;