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

import Fetch, {FetchConfig} from '../Fetch/index';
import {DEFAULT_HEADERS} from '../constant';
import {getAccessTokenUrl, getDefaultConfig, getCurrentEnvironment} from '../utils';
import {Resp, AsyncIterableType, AccessTokenResp} from '../interface';
import {getVersion1FetchOptions} from './version1';
import {getVersion2FetchOptions} from './version2';

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
    protected version?: string | number;
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
        Endpoint?: string;
        version?: string | number;
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
        this.version = options?.version ?? defaultConfig.version;
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

    protected async sendRequest(
        type: string,
        model: string,
        AKPath: string,
        requestBody: string,
        stream = false
    ): Promise<Resp | AsyncIterableType> {
        // 判断当前环境，node需要鉴权，浏览器不需要鉴权（需要设置proxy的baseUrl、consoleUrl）·
        const env = getCurrentEnvironment();

        let accessToken = this.access_token;
        if (!accessToken || this.expires_in < Date.now() / 1000) {
            const {access_token} = await this.getAccessToken();
            accessToken = access_token;
        }

        const params = {
            env,
            type,
            model,
            AKPath,
            requestBody,
            headers: this.headers,
            qianfanAccessKey: this.qianfanAccessKey,
            qianfanSecretKey: this.qianfanSecretKey,
            qianfanAk: this.qianfanAk,
            qianfanSk: this.qianfanSk,
            qianfanBaseUrl: this.qianfanBaseUrl,
            qianfanConsoleApiBaseUrl: this.qianfanConsoleApiBaseUrl,
            Endpoint: this.Endpoint,
            accessToken,
        };

        const fetchOptions
            = Number(this.version) === 2
                ? await getVersion2FetchOptions(params)
                : await getVersion1FetchOptions(params);
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
