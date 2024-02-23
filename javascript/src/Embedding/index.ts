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

import axios, {AxiosInstance} from 'axios';
import HttpClient from '../HttpClient';
import {api_base, DEFAULT_HEADERS, base_path} from '../constant';
import {getAccessToken, getRequestBody, getModelEndpoint, getIAMConfig, getDefaultConfig} from '../utils';
import {EmbeddingBody, EmbeddingResp} from '../interface';
import * as packageJson from '../../package.json';
import {modelInfoMap, EmbeddingModel} from './utils';

export class Eembedding {
    private QIANFAN_AK?: string;
    private QIANFAN_SK?: string;
    private QIANFAN_ACCESS_KEY?: string;
    private QIANFAN_SECRET_KEY?: string;
    private Type = 'IAM';
    private headers = DEFAULT_HEADERS;
    private axiosInstance: AxiosInstance;
    access_token = '';
    expires_in = 0;

    /**
     * 千帆大模型
     * @param options 配置选项，可选参数包括 QIANFAN_AK、QIANFAN_SK、QIANFAN_ACCESS_KEY、QIANFAN_SECRET_KEY
     */

    constructor(options?: { QIANFAN_AK?: string, QIANFAN_SK?: string, QIANFAN_ACCESS_KEY?: string, QIANFAN_SECRET_KEY?: string}) {
        const defaultConfig = getDefaultConfig();
        this.QIANFAN_AK = options?.QIANFAN_AK ?? defaultConfig.QIANFAN_AK;
        this.QIANFAN_SK = options?.QIANFAN_SK ?? defaultConfig.QIANFAN_SK;
        this.QIANFAN_ACCESS_KEY = options?.QIANFAN_ACCESS_KEY ?? defaultConfig.QIANFAN_ACCESS_KEY;
        this.QIANFAN_SECRET_KEY = options?.QIANFAN_SECRET_KEY ?? defaultConfig.QIANFAN_SECRET_KEY;
        this.axiosInstance = axios.create();
    }

    private async sendRequest(model: EmbeddingModel, body: EmbeddingBody): Promise<EmbeddingResp> {
        const endpoint = getModelEndpoint(model, modelInfoMap);
        const requestBody = getRequestBody(body, packageJson.version);
        // IAM鉴权
        if (this.QIANFAN_ACCESS_KEY && this.QIANFAN_SECRET_KEY) {
            const config = getIAMConfig(this.QIANFAN_ACCESS_KEY, this.QIANFAN_SECRET_KEY);
            const client = new HttpClient(config);
            const path = `${base_path}${endpoint}`;
            const response = await client.sendRequest('POST', path, requestBody, this.headers);
            return response as EmbeddingResp;
        }
        // AK/SK鉴权
        if (this.QIANFAN_AK && this.QIANFAN_SK) {
            const access = await getAccessToken(this.QIANFAN_AK, this.QIANFAN_SK, this.headers);
            // 重试问题初始化进入不了 TODO!!
            // if (access.expires_in < Date.now() / 1000) {
            const url = `${api_base}${endpoint}?access_token=${access.access_token}`;
            const options = {
                method: 'POST',
                url: url,
                headers: this.headers,
                data: requestBody
            };
            try {
                const resp = await this.axiosInstance.request(options);
                return resp.data as EmbeddingResp;
            }
            catch (error) {
                throw new Error(error);
            }
            // }
        }

        throw new Error('请设置AK/SK或QIANFAN_ACCESS_KEY/QIANFAN_SECRET_KEY');
    }

    public async embedding(body: EmbeddingBody, model: EmbeddingModel = 'Embedding-V1'): Promise<EmbeddingResp> {
        return this.sendRequest(model, body);
    }
}

export default Eembedding;