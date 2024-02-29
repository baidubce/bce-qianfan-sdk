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
import {getAccessTokenUrl, getIAMConfig, getDefaultConfig} from '../utils';
import {Stream} from '../streaming';
import {Resp, AsyncIterableType, AccessTokenResp} from '../interface';

export class BaseClient {
    protected controller: AbortController;
    protected QIANFAN_AK?: string;
    protected QIANFAN_SK?: string;
    protected QIANFAN_ACCESS_KEY?: string;
    protected QIANFAN_SECRET_KEY?: string;
    protected Endpoint?: string;
    protected headers = DEFAULT_HEADERS;
    protected axiosInstance: AxiosInstance;
    access_token = '';
    expires_in = 0;

    constructor(options?: {
        QIANFAN_AK?: string;
        QIANFAN_SK?: string;
        QIANFAN_ACCESS_KEY?: string;
        QIANFAN_SECRET_KEY?: string;
        Endpoint?: string;
    }) {
        const defaultConfig = getDefaultConfig();
        this.QIANFAN_AK = options?.QIANFAN_AK ?? defaultConfig.QIANFAN_AK;
        this.QIANFAN_SK = options?.QIANFAN_SK ?? defaultConfig.QIANFAN_SK;
        this.QIANFAN_ACCESS_KEY = options?.QIANFAN_ACCESS_KEY ?? defaultConfig.QIANFAN_ACCESS_KEY;
        this.QIANFAN_SECRET_KEY = options?.QIANFAN_SECRET_KEY ?? defaultConfig.QIANFAN_SECRET_KEY;
        this.Endpoint = options?.Endpoint;
        this.axiosInstance = axios.create();
        this.controller = new AbortController();
    }

    /**
     * 使用 AK，SK 生成鉴权签名（Access Token）
     * @return string 鉴权签名信息（Access Token）
     */

    private async getAccessToken(): Promise<AccessTokenResp> {
        const url = getAccessTokenUrl(this.QIANFAN_AK, this.QIANFAN_SK);
        try {
            const resp = await axios.post(url, {}, {headers: this.headers, withCredentials: false});
            const {data} = resp;
            if (data?.error) {
                throw new Error(data?.error_description || 'Failed to get access token');
            }
            this.access_token = resp.data.access_token ?? '';
            this.expires_in = resp.data.expires_in + Date.now() / 1000;
            return {
                access_token: resp.data.access_token,
                expires_in: resp.data.expires_in,
            };
        }
        catch (error) {
            const error_msg = `Failed to get access token: ${error && error.message}`;
            throw new Error(error_msg);
        }
    }

    protected async sendRequest(
        IAMpath: string,
        AKPath: string,
        requestBody: string,
        stream = false
    ): Promise<Resp | AsyncIterableType> {
        // IAM鉴权
        if (this.QIANFAN_ACCESS_KEY && this.QIANFAN_SECRET_KEY) {
            const config = getIAMConfig(this.QIANFAN_ACCESS_KEY, this.QIANFAN_SECRET_KEY);
            const client = new HttpClient(config);
            const response = await client.sendRequest('POST', IAMpath, requestBody, this.headers, stream);
            return response as Resp;
        }
        // AK/SK鉴权
        if (this.QIANFAN_AK && this.QIANFAN_SK) {
            if (this.expires_in < Date.now() / 1000) {
                await this.getAccessToken();
            }
            const url = `${AKPath}?access_token=${this.access_token}`;
            const options = {
                method: 'POST',
                url: url,
                headers: this.headers,
                data: requestBody,
            };
            // 流式处理
            if (stream) {
                try {
                    const sseStream: AsyncIterable<Resp> = Stream.fromSSEResponse(
                        await fetch(url, {
                            method: 'POST',
                            headers: this.headers,
                            body: requestBody as any,
                        }),
                        this.controller
                    ) as any;
                    return sseStream as AsyncIterableType;
                }
                catch (error) {
                    throw new Error(error);
                }
            }
            else {
                try {
                    const resp = await this.axiosInstance.request(options);
                    const {data} = resp;
                    if (data?.error) {
                        throw new Error(data?.error_description || 'Failed to getResult');
                    }
                    return resp.data as Resp;
                }
                catch (error) {
                    // 如果是 axios 请求相关的错误，直接抛出
                    if (axios.isAxiosError(error)) {
                        throw error;
                    }
                    throw new Error(`Request failed: ${error.message}`);
                }
            }
        }
        throw new Error('请设置AK/SK或QIANFAN_ACCESS_KEY/QIANFAN_SECRET_KEY');
    }
}
