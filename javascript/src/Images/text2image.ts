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
import {Text2ImageBody, Text2ImageResp} from '../interface';
import {text2ImageModelInfoMap} from './utils';
import {getPathAndBody, getUpperCaseModelAndModelMap} from '../utils';

class Text2Image extends BaseClient {
    /**
     * 文生图
     * @param body 续写请求体
     * @param model 续写模型，默认为 'ERNIE-Bot-turbo'
     * @returns 返回 Promise 对象，异步获取续写结果
     */
    public async text2Image(
        body: Text2ImageBody,
        model = 'Stable-Diffusion-XL'
    ): Promise<Text2ImageResp> {
        const {modelInfoMapUppercase, modelUppercase} = getUpperCaseModelAndModelMap(model, text2ImageModelInfoMap);
        const {IAMPath, AKPath, requestBody} = getPathAndBody({
            model: modelUppercase,
            modelInfoMap: modelInfoMapUppercase,
            baseUrl: this.qianfanBaseUrl,
            body,
            endpoint: this.Endpoint,
            type: 'text2image',
        });
        const resp = await this.sendRequest(IAMPath, AKPath, requestBody);
        return resp as Text2ImageResp;
    }
}

export default Text2Image;
