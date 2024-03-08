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
import {EmbeddingBody, EmbeddingResp} from '../interface';
import {modelInfoMap, EmbeddingModel} from './utils';
import {getPathAndBody} from '../utils';

class Eembedding extends BaseClient {
    /**
     * 向量化
     * @param body 请求体
     * @param model 向量化模型，默认为'Embedding-V1'
     * @returns Promise<Resp | AsyncIterable<Resp>>
     */
    public async embedding(body: EmbeddingBody, model: EmbeddingModel = 'Embedding-V1'): Promise<EmbeddingResp> {
        const {IAMPath, AKPath, requestBody} = getPathAndBody({
            model,
            modelInfoMap,
            baseUrl: this.qianfanBaseUrl,
            body,
            endpoint: this.Endpoint,
            type: 'embeddings',
        });
        const resp = await this.sendRequest(IAMPath, AKPath, requestBody);
        return resp as EmbeddingResp;
    }
}

export default Eembedding;
