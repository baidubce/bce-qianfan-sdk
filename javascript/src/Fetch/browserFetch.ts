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

import {Readable} from 'stream';
import {RETRY_CODE} from '../constant';
import {Stream} from '../streaming';
import {parseHeaders} from '../utils';

export type Headers = Record<string, string | null | undefined>;
export interface RequestOptions extends RequestInit {
    maxRetries?: number; // 最大重试次数
    timeout?: number; // 请求超时时间（毫秒）
    stream?: boolean | undefined;
}

type APIResponseProps = {
    response: Response;
    options: RequestOptions;
    controller: AbortController;
};

interface StreamWithTee {
    tee(): [ReadableStream, ReadableStream];
}

/**
 * 处理 API 响应的函数
 *
 * @param props API 响应的属性
 * @returns 返回处理后的结果
 */

export async function handleResponse<T>(props: APIResponseProps): Promise<T | StreamWithTee | null> {
    const {response, options} = props;
    const controller = props.controller ?? new AbortController();
    const contentType = response?.headers?.get('content-type');
    const isJSON = contentType?.includes('application/json') || contentType?.includes('application/vnd.api+json');
    const headers = parseHeaders(response.headers);
    if (isJSON) {
        const json = await response.json();
        return {
            headers,
            ...(json as T),
        };
    }
    if (options.stream) {
        // 明确指出返回类型为 StreamWithTee
        return Stream.fromSSEResponse(response, controller) as unknown as StreamWithTee;
    }
    if (response.status === 204) {
        return null;
    }
    const text = await response?.text();
    return {
        headers,
        ...(text as unknown as T),
    };
}

export const sleep = (ms: number) => new Promise(resolve => setTimeout(resolve, ms));

const validatePositiveInteger = (name: string, n: unknown): number => {
    if (typeof n !== 'number' || !Number.isInteger(n)) {
        throw new Error(`${name} must be an integer`);
    }
    if (n < 0) {
        throw new Error(`${name} must be a positive integer`);
    }
    return n;
};

export const castToError = (err: any): Error => {
    if (err instanceof Error) {
        return err;
    }
    return new Error(err);
};

export const safeJSON = (text: string) => {
    try {
        return JSON.parse(text);
    }
    catch (err) {
        return undefined;
    }
};

export class Fetch {
    maxRetries?: number;
    timeout?: number;
    retryMaxWaitInterval?: number;
    backoffFactor?: number;

    /**
     * 使用带有超时的 fetch 请求获取资源
     * @returns 返回 Promise<Response>，表示获取到的响应
     */

    constructor({
        maxRetries = 3,
        timeout = 600000,
        backoffFactor = 0,
        retryMaxWaitInterval = 120000,
    }: {
        maxRetries?: number | undefined;
        timeout?: number | undefined;
        backoffFactor?: number | undefined;
        retryMaxWaitInterval?: number | undefined;
    } = {}) {
        this.maxRetries = validatePositiveInteger('maxRetries', maxRetries);
        this.timeout = validatePositiveInteger('timeout', timeout);
        this.backoffFactor = backoffFactor;
        this.retryMaxWaitInterval = retryMaxWaitInterval;
    }
    async fetchWithTimeout(
        url: string,
        init: RequestInit | undefined,
        ms: number,
        controller: AbortController
    ): Promise<Response> {
        const {signal, ...options} = init || {};
        if (signal) {
            signal.addEventListener('abort', () => controller.abort());
        }

        const timeout = setTimeout(() => controller.abort(), ms);

        return fetch(url, {signal: controller.signal as any, ...(options as any)})
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP error, status = ${response.status}`);
                }
                return response;
            })
            .catch(error => {
                // console.error('Fetch request failed:', error.message);
                throw error;
            })
            .finally(() => {
                clearTimeout(timeout);
            });
    }

    /**
     * 发起请求并处理响应
     *
     * @param options 请求选项
     * @param retriesRemaining 剩余重试次数，可以为 null
     * @returns Promise<APIResponseProps> 响应对象，包含响应信息、请求选项和 AbortController 实例
     */
    async makeRequest(url: string, options: RequestOptions, retriesRemaining?: number): Promise<Response | any> {
        if (!retriesRemaining && retriesRemaining !== 0) {
            retriesRemaining = options.maxRetries ?? this.maxRetries;
        }

        if (options.signal?.aborted) {
            throw new Error('Request was aborted.');
        }
        const timeout = options.timeout ?? this.timeout;
        const controller = new AbortController();
        const response = await this.fetchWithTimeout(url, options, timeout, controller).catch(castToError);
        if (response instanceof Error) {
            if (options.signal?.aborted) {
                throw new Error('Request was aborted.');
            }
            if (response.name === 'AbortError') {
                throw new Error('Request timed out.');
            }
            throw new Error('Request timed out.' + response.message);
        }

        if (!response.ok) {
            if (retriesRemaining && this.shouldRetry(response)) {
                const retryMessage = `retrying, ${retriesRemaining} attempts remaining`;
                console.log(retryMessage);
                return this.retryRequest(url, options, retriesRemaining, response.headers as any);
            }
            const retryMessage = retriesRemaining ? '(error; no more retries left)' : '(error; not retryable)';
            throw new Error(retryMessage);
        }
        const res = await handleResponse({response, options, controller});
        if (typeof res === 'object' && res !== null && 'error_code' in res) {
            const resWithError = res as {error_code: number; error_description?: string};
            // 如果存在错误码且不需要重试，则直接抛出错误
            if (!RETRY_CODE.includes(resWithError.error_code)) {
                throw new Error(JSON.stringify(res));
            }
            // 网络正常的情况下API 336100（ServerHighLoad）、18 (QPSIimit)、336501（RPMLimitReached）、336502（TPMLimitReached）进行重试
            if (retriesRemaining && this.shouldRetryWithErrorCode(resWithError)) {
                return this.retryRequest(url, options, retriesRemaining, response.headers as any);
            }
        }
        // 流式
        if (options.stream && res instanceof Readable) {
            const [stream1, stream2] = (res as any).tee();
            return stream2;
        }
        return res;
    }

    /**
     * 判断是否应该重试请求
     *
     * @param response HTTP响应对象
     * @returns 返回布尔值，表示是否应该重试请求
     */
    private shouldRetry(response: Response): boolean {
        const shouldRetryHeader = response.headers.get('x-should-retry');
        if (shouldRetryHeader === 'true') {
            return true;
        }
        if (shouldRetryHeader === 'false') {
            return false;
        }
        if (response.status === 408) {
            return true;
        }
        if (response.status === 409) {
            return true;
        }
        if (response.status === 429) {
            return true;
        }
        if (response.status >= 500) {
            return true;
        }
        return false;
    }

    /**
     * 判断是否应该根据错误码进行重试
     *
     * @param data 包含错误码和错误描述的对象
     * @returns 如果错误码在可重试的错误码列表中，则返回true，否则返回false
     */
    private shouldRetryWithErrorCode(data: {error_code?: number; error_description?: string}): boolean {
        // 对于已识别为可重试的错误码继续重试
        return RETRY_CODE.includes(data?.error_code ?? 0);
    }

    /**
     * 重试请求
     *
     * @param options 请求选项
     * @param retriesRemaining 剩余重试次数
     * @param responseHeaders 响应头，可选
     * @returns 返回 API 响应属性
     */
    private async retryRequest(
        url: string,
        options: RequestOptions,
        retriesRemaining: number,
        responseHeaders?: Headers | undefined
    ): Promise<Response | any> {
        let timeoutMillis: number | undefined;
        const retryAfterMillisHeader = responseHeaders?.['retry-after-ms'];
        if (retryAfterMillisHeader) {
            const timeoutMs = parseFloat(retryAfterMillisHeader);
            if (!Number.isNaN(timeoutMs)) {
                timeoutMillis = timeoutMs;
            }
        }
        // Retry-After header: https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Retry-After
        const retryAfterHeader = responseHeaders?.['retry-after'];
        if (retryAfterHeader && !timeoutMillis) {
            const timeoutSeconds = parseFloat(retryAfterHeader);
            if (!Number.isNaN(timeoutSeconds)) {
                timeoutMillis = timeoutSeconds * 1000;
            }
            else {
                timeoutMillis = Date.parse(retryAfterHeader) - Date.now();
            }
        }
        if (!(timeoutMillis && 0 <= timeoutMillis && timeoutMillis < 60 * 1000)) {
            const maxRetries = options.maxRetries ?? this.maxRetries;
            timeoutMillis = this.calculateDefaultRetryTimeoutMillis(retriesRemaining, maxRetries ?? 0);
        }
        await sleep(timeoutMillis);
        return this.makeRequest(url, options, retriesRemaining - 1);
    }

    /**
     * 计算默认的重试超时时间（毫秒）
     *
     * @param retriesRemaining 剩余重试次数
     * @param maxRetries 最大重试次数
     * @returns 返回重试超时时间（毫秒）
     */
    private calculateDefaultRetryTimeoutMillis(retriesRemaining: number, maxRetries: number): number {
        // 计算当前尝试的次数
        const attempt = maxRetries - retriesRemaining;
        // 应用指数退避算法，并确保不超过最大值
        const sleepSeconds = Math.min(this.retryMaxWaitInterval, this.backoffFactor * Math.pow(2, attempt));
        // 应用一些抖动，最多占用重试时间的25%
        const jitter = 1 - Math.random() * 0.25;
        // 返回重试间隔的毫秒值
        return sleepSeconds * jitter * 1000;
    }
}

export default Fetch;
