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
import {Image2TextBody, RespBase} from '../interface';
import {image2TextModelInfoMap} from './utils';
import {getPathAndBody, getUpperCaseModelAndModelMap} from '../utils';

class Image2Text extends BaseClient {
    /**
     * 图生文
     * @param body 请求体
     * @returns 返回图像转文本
     */
    public async image2Text(
        body: Image2TextBody,
        model = 'Fuyu-8B'
    ): Promise<RespBase> {
        const {modelInfoMapUppercase, modelUppercase} = getUpperCaseModelAndModelMap(model, image2TextModelInfoMap);
        const {IAMPath, AKPath, requestBody} = getPathAndBody({
            model: modelUppercase,
            modelInfoMap: modelInfoMapUppercase,
            baseUrl: this.qianfanBaseUrl,
            body,
            endpoint: this.Endpoint,
            type: 'image2text',
        });
        const resp = await this.sendRequest(IAMPath, AKPath, requestBody);
        return resp as RespBase;
    }
}

export default Image2Text;
