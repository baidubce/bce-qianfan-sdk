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
import { modelInfoMap, EmbeddingModel } from './utils';
import { api_base, DEFAULT_HEADERS, base_path } from '../constant';
import {getAccessToken, getRequestBody, getModelEndpoint, getIAMConfig} from '../utils';
import { EmbeddingBody, EmbeddingResp } from '../interface';
import * as packageJson from '../../package.json';

export class Eembedding {
    private API_KEY: string;
    private SECRET_KEY: string;
    private Type: string = 'IAM';
    private headers = DEFAULT_HEADERS;
    private axiosInstance: AxiosInstance;
    access_token: string = '';
    expires_in: number = 0;

    /**
     * 千帆大模型
     * @param API_KEY API Key，IAM、AK/SK 鉴权时必填
     * @param SECRET_KEY Secret Key，IAM、AK/SK 鉴权时必填
     * @param Type 鉴权方式，默认IAM鉴权，如果使用AK/SK鉴权，请设置为'AK'
     */

    constructor(API_KEY: string, SECRET_KEY: string, Type: string = 'IAM') {
        this.API_KEY = API_KEY;
        this.SECRET_KEY = SECRET_KEY;
        this.Type = Type
        this.axiosInstance = axios.create();
    }

    private async sendRequest(model: EmbeddingModel, body: EmbeddingBody): Promise<EmbeddingResp> {
        const endpoint = getModelEndpoint(model, modelInfoMap);
        const requestBody = getRequestBody(body, packageJson.version);
        // IAM鉴权
        if (this.Type === 'IAM') {
            const config = getIAMConfig(this.API_KEY, this.SECRET_KEY);
            const client = new HttpClient(config);
            const path = `${base_path}${endpoint}`;
            const response = await client.sendRequest('POST', path, requestBody, this.headers);
            return response as EmbeddingResp;
        }
        // AK/SK鉴权    
        if (this.Type === 'AK') {
            const access = await getAccessToken(this.API_KEY, this.SECRET_KEY, this.headers);
            // 重试问题初始化进入不了 TODO!!
            // if (access.expires_in < Date.now() / 1000) { 
                const url = `${api_base}${endpoint}?access_token=${access.access_token}`;
                const options = {
                    method: 'POST',
                    url: url,
                    headers: this.headers,
                    data: requestBody
                }
                try {
                    const resp = await this.axiosInstance.request(options);
                    return resp.data as EmbeddingResp;
                } catch (error) {
                    throw new Error(error);
                }
            // }
        }

        throw new Error(`Unsupported authentication type: ${this.Type}`);
    }

    public async embedding(body: EmbeddingBody, model: EmbeddingModel = 'Embedding-V1'): Promise<EmbeddingResp> {
       return this.sendRequest(model, body);
    }
}

export default Eembedding;