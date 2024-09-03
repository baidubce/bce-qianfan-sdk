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

import HttpClient from '../HttpClient';
import Fetch, {FetchConfig} from '../Fetch/index';
import {DEFAULT_HEADERS} from '../constant';
import {getAccessTokenUrl, getIAMConfig, getDefaultConfig, getPath, getCurrentEnvironment} from '../utils';
import {Resp, AsyncIterableType, AccessTokenResp} from '../interface';
import DynamicModelEndpoint from '../DynamicModelEndpoint';

export class BaseClient {
    protected controller: AbortController;
    protected qianfanAk?: string;
    protected qianfanSk?: string;
    protected qianfanAccessKey?: string;
    protected qianfanSecretKey?: string;
    protected qianfanBaseUrl?: string;
    protected qianfanConsoleApiBaseUrl?: string;
    protected qianfanLlmApiRetryTimeout?: string;
    protected qianfanLlmApiRetryBackoffFactor?: string;
    protected qianfanLlmApiRetryCount?: string;
    protected qianfanLlmRetryMaxWaitInterval?: string;
    protected Endpoint?: string;
    protected headers = DEFAULT_HEADERS;
    protected fetchInstance;
    protected fetchConfig: FetchConfig;
    protected enableOauth: boolean;
    access_token = '';
    expires_in = 0;

    constructor(options?: {
        QIANFAN_AK?: string;
        QIANFAN_SK?: string;
        QIANFAN_ACCESS_KEY?: string;
        QIANFAN_SECRET_KEY?: string;
        QIANFAN_BASE_URL?: string;
        QIANFAN_CONSOLE_API_BASE_URL?: string;
        QIANFAN_LLM_API_RETRY_TIMEOUT?: string;
        QIANFAN_LLM_API_RETRY_BACKOFF_FACTOR?: string;
        QIANFAN_LLM_API_RETRY_COUNT?: string;
        QIANFAN_LLM_RETRY_MAX_WAIT_INTERVAL?: string;
        ENABLE_OAUTH: boolean;
        Endpoint?: string;
    }) {
        const defaultConfig = getDefaultConfig();
        this.qianfanAk = options?.QIANFAN_AK ?? defaultConfig.QIANFAN_AK;
        this.qianfanSk = options?.QIANFAN_SK ?? defaultConfig.QIANFAN_SK;
        this.qianfanAccessKey = options?.QIANFAN_ACCESS_KEY ?? defaultConfig.QIANFAN_ACCESS_KEY;
        this.qianfanSecretKey = options?.QIANFAN_SECRET_KEY ?? defaultConfig.QIANFAN_SECRET_KEY;
        this.Endpoint = options?.Endpoint;
        this.qianfanBaseUrl = options?.QIANFAN_BASE_URL ?? defaultConfig.QIANFAN_BASE_URL;
        this.qianfanConsoleApiBaseUrl
            = options?.QIANFAN_CONSOLE_API_BASE_URL ?? defaultConfig.QIANFAN_CONSOLE_API_BASE_URL;
        this.qianfanLlmApiRetryTimeout
            = options?.QIANFAN_LLM_API_RETRY_TIMEOUT ?? defaultConfig.QIANFAN_LLM_API_RETRY_TIMEOUT;
        this.qianfanLlmApiRetryBackoffFactor
            = options?.QIANFAN_LLM_API_RETRY_BACKOFF_FACTOR ?? defaultConfig.QIANFAN_LLM_API_RETRY_BACKOFF_FACTOR;
        this.qianfanLlmApiRetryCount
            = options?.QIANFAN_LLM_API_RETRY_COUNT ?? defaultConfig.QIANFAN_LLM_API_RETRY_COUNT;
        this.enableOauth = options?.ENABLE_OAUTH ?? defaultConfig.ENABLE_OAUTH;
        this.controller = new AbortController();
        this.fetchInstance = new Fetch({
            maxRetries: Number(this.qianfanLlmApiRetryCount),
            timeout: Number(this.qianfanLlmApiRetryTimeout),
            backoffFactor: Number(this.qianfanLlmApiRetryBackoffFactor),
            retryMaxWaitInterval: Number(this.qianfanLlmRetryMaxWaitInterval),
        });
    }

    /**
     * 使用 AK，SK 生成鉴权签名（Access Token）
     * @return string 鉴权签名信息（Access Token）
     */

    private async getAccessToken(): Promise<AccessTokenResp> {
        const url = getAccessTokenUrl(this.qianfanAk, this.qianfanSk, this.qianfanBaseUrl);
        try {
            const resp = await this.fetchInstance.makeRequest(url, {
                headers: this.headers,
                method: 'POST',
            });
            this.access_token = resp.access_token ?? '';
            this.expires_in = resp.expires_in + Date.now() / 1000;
            return {
                access_token: resp.access_token,
                expires_in: resp.expires_in,
            };
        }
        catch (error) {
            const error_msg = `Failed to get access token: ${error && error.message}`;
            throw new Error(error_msg);
        }
    }

    /**
     * 获取 IAM 路径 （配置proxy情况下）
     *
     * @param type 路径类型
     * @param model 模型名称
     * @returns 返回 IAM 路径
     * @throws 当 qianfanBaseUrl 包含 'aip.baidubce.com' 时，抛出错误提示设置 proxy 的 baseUrl
     * @throws 当 qianfanConsoleApiBaseUrl 未设置时，抛出错误提示未设置 qianfanConsoleApiBaseUrl
     * @throws 当 Endpoint 未设置且 qianfanConsoleApiBaseUrl 不包含 'qianfan.baidubce.com' 时，抛出错误提示未设置 Endpoint
     */
    private async getIAMPath(type, model) {
        if (this.qianfanBaseUrl.includes('aip.baidubce.com')) {
            throw new Error('请设置proxy的baseUrl');
        }
        const dynamicModelEndpoint = new DynamicModelEndpoint(
            null,
            this.qianfanConsoleApiBaseUrl,
            this.qianfanBaseUrl
        );
        return await dynamicModelEndpoint.getEndpoint(type, model);
    }

    public async getAllModels(type): Promise<string[]> {
        const dynamicModelEndpoint = new DynamicModelEndpoint(
            null,
            this.qianfanConsoleApiBaseUrl,
            this.qianfanBaseUrl
        );
        const map = await dynamicModelEndpoint.getDynamicMap(type);
        const keysArray: string[] = Array.from(map.keys()); // 将Map的键转换为数组
        return keysArray;
    }

    protected async sendRequest(
        type: string,
        model: string,
        AKPath: string,
        requestBody: string,
        stream = false
    ): Promise<Resp | AsyncIterableType> {
        let fetchOptions;
        // 如果enableOauth开启， 则放开鉴权
        if (getCurrentEnvironment() === 'node' || this.enableOauth) {
            // 检查鉴权信息
            if (!(this.qianfanAccessKey && this.qianfanSecretKey) && !(this.qianfanAk && this.qianfanSk)) {
                throw new Error('请设置AK/SK或QIANFAN_ACCESS_KEY/QIANFAN_SECRET_KEY');
            }
            // IAM鉴权
            if (this.qianfanAccessKey && this.qianfanSecretKey) {
                const config = getIAMConfig(this.qianfanAccessKey, this.qianfanSecretKey, this.qianfanBaseUrl);
                const client = new HttpClient(config);
                const dynamicModelEndpoint = new DynamicModelEndpoint(
                    client,
                    this.qianfanConsoleApiBaseUrl,
                    this.qianfanBaseUrl
                );
                let IAMPath = '';
                if (this.Endpoint) {
                    IAMPath = getPath({
                        Authentication: 'IAM',
                        api_base: this.qianfanBaseUrl,
                        endpoint: this.Endpoint,
                        type,
                    });
                }
                else {
                    IAMPath = await dynamicModelEndpoint.getEndpoint(type, model);
                }
                if (!IAMPath) {
                    throw new Error(`${model} is not supported`);
                }
                fetchOptions = await client.getSignature({
                    httpMethod: 'POST',
                    path: IAMPath,
                    body: requestBody,
                    headers: this.headers,
                });
            }
            // AK/SK鉴权
            if (this.qianfanAk && this.qianfanSk) {
                if (!AKPath) {
                    throw new Error(`${model} is not supported`);
                }
                if (this.expires_in < Date.now() / 1000) {
                    await this.getAccessToken();
                }
                const url = `${AKPath}?access_token=${this.access_token}`;
                fetchOptions = {
                    url: url,
                    method: 'POST',
                    headers: this.headers,
                    body: requestBody,
                };
            }
        }
        else {
            // 设置了proxy url走prxoy
            const IAMPath = await this.getIAMPath(type, model);
            if (!IAMPath) {
                throw new Error(`${model} is not supported`);
            }
            fetchOptions = {
                url: `${this.qianfanBaseUrl}${IAMPath}`,
                method: 'POST',
                headers: this.headers,
                body: requestBody,
            };
        }
        try {
            const {url, ...rest} = fetchOptions;
            const resp = await this.fetchInstance.makeRequest(url, {...rest, stream});
            return resp;
        }
        catch (error) {
            throw error;
        }
    }
}
