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
import {RespBase, Image2TextBody, Text2ImageResp} from '../interface';
import {getPathAndBody} from '../utils';

class Image2Text extends BaseClient {
    /**
     * 文生图
     * @param body 续写请求体
     * @param model 续写模型，默认为 'ERNIE-Bot-turbo'
     * @returns 返回 Promise 对象，异步获取续写结果
     */
    public async image2Text(
        body: Image2TextBody
    ): Promise<RespBase> {
        const {IAMPath, AKPath, requestBody} = getPathAndBody({
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
