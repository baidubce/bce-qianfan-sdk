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
import {Fetch, FetchConfig} from '../Fetch';
import {TokenLimiter} from '../Limiter';
import {DEFAULT_HEADERS} from '../constant';
import {getAccessTokenUrl, getIAMConfig, getDefaultConfig, calculateRetryDelay, isOpenTpm} from '../utils';
import {Stream} from '../streaming';
import {Resp, AsyncIterableType, AccessTokenResp, RespBase} from '../interface';

export class BaseClient {
    protected controller: AbortController;
    protected qianfanAk?: string;
    protected qianfanSk?: string;
    protected qianfanAccessKey?: string;
    protected qianfanSecretKey?: string;
    protected qianfanBaseUrl?: string;
    protected qianfanLlmApiRetryTimeout?: string;
    protected qianfanLlmApiRetryBackoffFactor?: string;
    protected qianfanLlmApiRetryCount?: string;
    protected qianfanLlmRetryMaxWaitInterval?: string;
    protected Endpoint?: string;
    protected headers = DEFAULT_HEADERS;
    protected fetchInstance: Fetch;
    protected fetchConfig: FetchConfig;
    private tokenLimiter: TokenLimiter;
    access_token = '';
    expires_in = 0;

    constructor(options?: {
        QIANFAN_AK?: string;
        QIANFAN_SK?: string;
        QIANFAN_ACCESS_KEY?: string;
        QIANFAN_SECRET_KEY?: string;
        QIANFAN_BASE_URL?: string;
        QIANFAN_LLM_API_RETRY_TIMEOUT?: string;
        QIANFAN_LLM_API_RETRY_BACKOFF_FACTOR?: string;
        QIANFAN_LLM_API_RETRY_COUNT?: string;
        QIANFAN_LLM_RETRY_MAX_WAIT_INTERVAL?: string;
        Endpoint?: string;
    }) {
        const defaultConfig = getDefaultConfig();
        this.qianfanAk = options?.QIANFAN_AK ?? defaultConfig.QIANFAN_AK;
        this.qianfanSk = options?.QIANFAN_SK ?? defaultConfig.QIANFAN_SK;
        this.qianfanAccessKey = options?.QIANFAN_ACCESS_KEY ?? defaultConfig.QIANFAN_ACCESS_KEY;
        this.qianfanSecretKey = options?.QIANFAN_SECRET_KEY ?? defaultConfig.QIANFAN_SECRET_KEY;
        this.Endpoint = options?.Endpoint;
        this.qianfanBaseUrl = options?.QIANFAN_BASE_URL ?? defaultConfig.QIANFAN_BASE_URL;
        this.qianfanLlmApiRetryTimeout
            = options?.QIANFAN_LLM_API_RETRY_TIMEOUT ?? defaultConfig.QIANFAN_LLM_API_RETRY_TIMEOUT;
        this.qianfanLlmApiRetryBackoffFactor
            = options?.QIANFAN_LLM_API_RETRY_BACKOFF_FACTOR ?? defaultConfig.QIANFAN_LLM_API_RETRY_BACKOFF_FACTOR;
        this.qianfanLlmApiRetryCount
            = options?.QIANFAN_LLM_API_RETRY_COUNT ?? defaultConfig.QIANFAN_LLM_API_RETRY_COUNT;
        this.controller = new AbortController();
        this.fetchConfig = {
            retries: Number(this.qianfanLlmApiRetryCount),
            timeout: Number(this.qianfanLlmApiRetryTimeout),
            retryDelay: attempt =>
                calculateRetryDelay(
                    attempt,
                    Number(this.qianfanLlmApiRetryBackoffFactor),
                    Number(this.qianfanLlmRetryMaxWaitInterval)
                ),
        };
        this.fetchInstance = new Fetch(this.fetchConfig);
        this.tokenLimiter = new TokenLimiter();
    }

    /**
     * 使用 AK，SK 生成鉴权签名（Access Token）
     * @return string 鉴权签名信息（Access Token）
     */

    private async getAccessToken(): Promise<AccessTokenResp> {
        const url = getAccessTokenUrl(this.qianfanAk, this.qianfanSk, this.qianfanBaseUrl);
        try {
            const resp = await this.fetchInstance.fetchWithRetry(url, {headers: this.headers, method: 'POST'});
            const data = (await resp.json()) as AccessTokenResp;
            if (data?.error) {
                throw new Error(data?.error_description || 'Failed to get access token');
            }
            this.access_token = data.access_token ?? '';
            this.expires_in = data.expires_in + Date.now() / 1000;
            return {
                access_token: data.access_token,
                expires_in: data.expires_in,
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
        // 检查鉴权信息
        if (!(this.qianfanAccessKey && this.qianfanSecretKey) && !(this.qianfanAk && this.qianfanSk)) {
            throw new Error('请设置AK/SK或QIANFAN_ACCESS_KEY/QIANFAN_SECRET_KEY');
        }

        let fetchOptions;
        // IAM鉴权
        if (this.qianfanAccessKey && this.qianfanSecretKey) {
            const config = getIAMConfig(this.qianfanAccessKey, this.qianfanSecretKey, this.qianfanBaseUrl);
            const client = new HttpClient(config);
            fetchOptions = await client.getSignature({
                httpMethod: 'POST',
                path: IAMpath,
                body: requestBody,
                headers: this.headers,
            });
        }
        // AK/SK鉴权
        if (this.qianfanAk && this.qianfanSk) {
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

        // 计算请求token
        const tokens = this.tokenLimiter.calculateTokens(requestBody);
        const hasToken = await this.tokenLimiter.acquireTokens(tokens);
        // 满足token限制
        if (hasToken) {
            try {
                const resp = await this.fetchInstance.fetchWithRetry(fetchOptions.url, fetchOptions);
                const val = this.getTpmHeader(resp.headers);
                let usedTokens = 0;
                if (stream) {
                    const sseStream = Stream.fromSSEResponse(resp, this.controller);
                    const [stream1, stream2] = sseStream.tee();
                    if (isOpenTpm(val)) {
                        const updateTokensAsync = async () => {
                            for await (const data of stream1) {
                                const typedData = data as RespBase;
                                if (typedData.is_end) {
                                    usedTokens = typedData?.usage?.total_tokens;
                                    await this.tokenLimiter.acquireTokens(usedTokens - tokens);
                                    break;
                                }
                            }
                        };
                        setTimeout(updateTokensAsync, 0);
                    }
                    return stream2 as AsyncIterableType;
                }
                const data = await resp.json();
                setTimeout(async () => {
                    usedTokens = this.getUsedTokens(data);
                    await this.tokenLimiter.acquireTokens(usedTokens - tokens);
                }, 0);
                return data as any;
            }
            catch (error) {
                throw error;
            }
        }
        else {
            throw new Error('Token limit exceeded');
        }
    }

    getTpmHeader(headers: any): void {
        const val = headers.get('x-ratelimit-limit-tokens') ?? '0';
        this.tokenLimiter.resetTokens(val);
        return val;
    }

    async getStreamUsedTokens(data: AsyncIterableType): Promise<number> {
        let usedTokens = 0;
        for await (const chunk of data as AsyncIterableType) {
            if (chunk.is_end) {
                usedTokens = chunk?.usage?.total_tokens;
            }
        }
        return usedTokens ?? 0;
    }
    getUsedTokens(data: Resp): number {
        const usage = data?.usage?.total_tokens;
        return usage ?? 0;
    }
}
