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
import {modelInfoMap} from './utilts';
import {getPathAndBody, getUpperCaseModelAndModelMap} from '../utils';
import {RerankerBody, RerankerResp} from '../interface';
import {getTypeMap, typeModelEndpointMap} from '../DynamicModelEndpoint/utils';
import {ModelType} from '../enum';

class Reranker extends BaseClient {

    public async reranker(body: RerankerBody, model = 'bce-reranker-base_v1'): Promise<RerankerResp> {
        const {modelInfoMapUppercase, modelUppercase} = getUpperCaseModelAndModelMap(model, modelInfoMap);
        const type = ModelType.RERANKER;
        const modelKey = model.toLowerCase();
        const typeMap = getTypeMap(typeModelEndpointMap, type) ?? new Map();
        const endPoint = typeMap.get(modelKey) || '';
        const {AKPath, requestBody} = getPathAndBody({
            model: modelUppercase,
            modelInfoMap: modelInfoMapUppercase,
            baseUrl: this.qianfanBaseUrl,
            body,
            endpoint: this.Endpoint ?? endPoint,
            type,
        });
        const resp = await this.sendRequest(type, model, AKPath, requestBody);
        return resp as RerankerResp;
    }
}

export default Reranker;