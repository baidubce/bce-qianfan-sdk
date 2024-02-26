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
import {DEFAULT_HEADERS} from '../constant';
import {getAccessToken, getRequestBody, getIAMConfig, getPath, getDefaultConfig} from '../utils';
import {Stream} from '../streaming';
import {RespBase, CompletionBody} from '../interface';
import * as packageJson from '../../package.json';
import {CompletionModel, modelInfoMap} from './utils';

export class Completions {
    private controller: AbortController;
    private QIANFAN_AK?: string;
    private QIANFAN_SK?: string;
    private QIANFAN_ACCESS_KEY?: string;
    private QIANFAN_SECRET_KEY?: string;
    private Endpoint?: string = '';
    private headers = DEFAULT_HEADERS;
    private axiosInstance: AxiosInstance;
    access_token = '';
    expires_in = 0;

    /**
     * 千帆大模型
     * @param options 配置选项，可选参数包括 QIANFAN_AK、QIANFAN_SK、QIANFAN_ACCESS_KEY、QIANFAN_SECRET_KEY、Endpoint
     */

    constructor(options?: { QIANFAN_AK?: string, QIANFAN_SK?: string, QIANFAN_ACCESS_KEY?: string, QIANFAN_SECRET_KEY?: string, Endpoint?: string}) {
        const defaultConfig = getDefaultConfig();
        this.QIANFAN_AK = options?.QIANFAN_AK ?? defaultConfig.QIANFAN_AK;
        this.QIANFAN_SK = options?.QIANFAN_SK ?? defaultConfig.QIANFAN_SK;
        this.QIANFAN_ACCESS_KEY = options?.QIANFAN_ACCESS_KEY ?? defaultConfig.QIANFAN_ACCESS_KEY;
        this.QIANFAN_SECRET_KEY = options?.QIANFAN_SECRET_KEY ?? defaultConfig.QIANFAN_SECRET_KEY;
        this.Endpoint = options?.Endpoint;
        this.axiosInstance = axios.create();
    }

    private async sendRequest(model: CompletionModel, body: CompletionBody, stream = false, endpoint?:string): Promise<RespBase | AsyncIterable<RespBase>> {
        const path = getPath(model, modelInfoMap, endpoint, 'completions');
        const requestBody = getRequestBody(body, packageJson.version);
        // IAM鉴权
        if (this.QIANFAN_ACCESS_KEY && this.QIANFAN_SECRET_KEY) {
            const config = getIAMConfig(this.QIANFAN_ACCESS_KEY, this.QIANFAN_SECRET_KEY);
            const client = new HttpClient(config);
            const response = await client.sendRequest('POST', path, requestBody, this.headers, stream);
            return response as RespBase;
        }
        // AK/SK鉴权
        if (this.QIANFAN_AK && this.QIANFAN_SK) {
            const access = await getAccessToken(this.QIANFAN_AK, this.QIANFAN_SK, this.headers);
            // 重试问题初始化进入不了 TODO!!
            // if (access.expires_in < Date.now() / 1000) {
            const url = `${path}?access_token=${access.access_token}`;
            const options = {
                method: 'POST',
                url: url,
                headers: this.headers,
                data: requestBody
            };
            // 流式处理
            if (stream) {
                try {
                    const sseStream: AsyncIterable<RespBase> = Stream.fromSSEResponse(await fetch(url, {
                        method: 'POST',
                        headers: this.headers,
                        body: requestBody
                    }), this.controller) as any;
                    return sseStream;
                }
                catch (error) {
                    throw new Error(error);
                }
            }
            else {
                try {
                    const resp = await this.axiosInstance.request(options);
                    return resp.data as RespBase;
                }
                catch (error) {
                    throw new Error(error);
                }
            }
            // }
        }

        throw new Error('请设置AK/SK或QIANFAN_ACCESS_KEY/QIANFAN_SECRET_KEY');
    }

    public async completions(body: CompletionBody, model: CompletionModel = 'ERNIE-Bot-turbo'): Promise<RespBase | AsyncIterable<RespBase>> {
        const stream = body.stream ?? false;
        return this.sendRequest(model, body, stream, this.Endpoint);
    }
}

export default Completions;