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

import RateLimiter from '../RateLimiter';
import {RETRY_CODE} from '../constant';

type RetryOnFunction = (attempt: number, error: Error | null, response: Response | null) => boolean;

export interface FetchConfig {
    retries: number;
    timeout: number;
    retryDelay: (attempt: number) => number;
}

export interface RequestOptions extends RequestInit {
    retries?: number; // 最大重试次数
    retryDelay?: number | ((attempt: number) => number); // 重试之间的延迟策略
    retryOn?: Array<number> | RetryOnFunction; // 定义哪些情况应触发重试
    timeout?: number; // 请求超时时间（毫秒）
}

export class Fetch {
    private rateLimiter: RateLimiter;
    retries: number;
    timeout: number;
    retryDelay: number | ((attempt: number) => number);
    retryOn: Array<number> | RetryOnFunction;

    constructor({
        retries = 3,
        timeout = 5000,
        retryDelay = (attempt: number) => 1000 * Math.pow(2, attempt), // 指数回避策略
        retryOn = [] as Array<number> | RetryOnFunction,
    } = {}) {
        this.retries = retries;
        this.timeout = timeout;
        this.retryDelay = retryDelay;
        this.retryOn = retryOn;
        this.rateLimiter = new RateLimiter();
    }

    async fetchWithRetry(url: string, options: RequestOptions = {}): Promise<Response> {
        const fetchWithTimeout = async (url: string, options: RequestOptions): Promise<Response> => {
            const controller = new AbortController();
            const timer = setTimeout(() => controller.abort(), options.timeout || this.timeout);
            options.signal = controller.signal;

            try {
                const response = await fetch(url, options);
                return response;
            }
            catch (error) {
                throw error;
            }
            finally {
                clearTimeout(timer);
            }
        };

        const isJsonResponse = (response: Response) => {
            const contentType = response.headers.get('Content-Type');
            return contentType && contentType.includes('application/json');
        };

        const shouldRetry = async (response?: Response, error?: Error): Promise<boolean> => {
            // TODO ！！！处理或决定是否重试中断的请求
            if (error?.name === 'AbortError') {
                return false;
            }
            if (response?.ok && isJsonResponse(response)) {
                try {
                    const data = await response.clone().json();
                    // 对于不应该重试的特定错误码抛出异常
                    if (data?.error_code && !RETRY_CODE.includes(data?.error_code)) {
                        const errorMessage = JSON.stringify(data);
                        throw new Error(errorMessage);
                    }
                    // 对于已识别为可重试的错误码继续重试
                    return RETRY_CODE.includes(data?.error_code);
                }
                catch (jsonError) {
                    throw new Error(jsonError);
                }
            }
            // 对于非 JSON 响应或响应中没有特定错误码的默认行为
            return false;
        };

        const makeRequest = async (): Promise<Response> => {
            let attempt = 0;
            while (attempt < this.retries) {
                try {
                    const response = await this.rateLimiter.schedule(() =>
                        fetchWithTimeout(url, {...options, timeout: this.timeout})
                    );
                    const rpm = response.headers.get('X-Ratelimit-Limit-Requests');
                    const tpm = response.headers.get('X-Ratelimit-Limit-Tokens');
                    if (rpm || tpm) {
                        this.rateLimiter.updateLimits(undefined, Number(rpm), Number(tpm));
                    }
                    // 注意：现在 shouldRetry 可能会直接抛出异常
                    const retry = await shouldRetry(response);
                    if (retry) {
                        attempt++;
                        const delay
                            = typeof this.retryDelay === 'function' ? this.retryDelay(attempt) : this.retryDelay;
                        await new Promise(resolve => setTimeout(resolve, delay));
                        continue;
                    }
                    return response;
                }
                catch (error) {
                    // 捕获由 shouldRetry 抛出的异常或其他异常
                    if (await shouldRetry(undefined, error)) {
                        attempt++;
                        const delay
                            = typeof this.retryDelay === 'function' ? this.retryDelay(attempt) : this.retryDelay;
                        await new Promise(resolve => setTimeout(resolve, delay));
                        continue;
                    }
                    throw error;
                }
            }
            throw new Error('All retry attempts failed.');
        };

        return makeRequest();
    }
}

export default Fetch;
