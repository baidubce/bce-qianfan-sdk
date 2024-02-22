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

import axios, {AxiosInstance, AxiosRequestConfig, AxiosResponse} from 'axios';
import * as process from 'process';
import * as http from 'http';
import * as stream from 'stream';
import {EventEmitter} from 'events';
import * as u from 'underscore';
import * as Q from 'q';
import {URL} from 'url';
import createDebug from 'debug';
import * as packageJson from '../../package.json';

import {Stream} from '../streaming';
import Auth from './auth';
import * as H from './headers';
import {urlObjectToPlainObject} from './strings';

const debug = createDebug('bce-sdk:HttpClient');
// 获取版本号
const version = packageJson.version;
class HttpClient extends EventEmitter {
    private controller: AbortController;
    private readonly defaultHeaders: Record<string, any> = {
        [H.CONNECTION]: 'close',
        [H.CONTENT_TYPE]: 'application/json; charset=UTF-8',
        // 检查是否在浏览器环境中
        [H.USER_AGENT]: typeof navigator !== 'undefined' && navigator.userAgent
            ? navigator.userAgent
            : `bce-sdk-nodejs/${version}/${process.platform}/${process.version}`,
        [H.X_BCE_DATE]: new Date().toISOString().replace(/\.\d+Z$/, 'Z')
    };
    private axiosInstance: AxiosInstance;
    constructor(private config: any) {
        super();
        this.axiosInstance = axios.create();
        this.controller = new AbortController();
    }
    sendRequest(
        httpMethod: string,
        path: string,
        body?: string | Buffer | stream.Readable,
        headers?: Record<string, any>,
        outputStream?: boolean | stream.Writable,
        params?: Record<string, any>,
        signFunction?: () => [string, string] | string
    ): Q.Promise<any> {
        httpMethod = httpMethod.toUpperCase();
        const requestUrl = this._getRequestUrl(path, params);
        const _headers = u.extend({}, this.defaultHeaders, headers);
        if (!_headers.hasOwnProperty(H.CONTENT_LENGTH)) {
            const contentLength = this._guessContentLength(body);
            if (!(contentLength === 0 && /GET|HEAD/i.test(httpMethod))) {
                // 如果是 GET 或 HEAD 请求，并且 Content-Length 是 0，那么 Request Header 里面就不要出现 Content-Length
                // 否则本地计算签名的时候会计算进去，但是浏览器发请求的时候不一定会有，此时导致 Signature Mismatch 的情况
                _headers[H.CONTENT_LENGTH] = contentLength;
            }
        }
        const client = this;
        const url = new URL(requestUrl) as any;
        _headers[H.HOST] = url.host;
        const options = urlObjectToPlainObject(url, httpMethod, _headers);
        return this.setAuthorizationHeader(signFunction, _headers, options).then(() => {
            debug('options = %j', options);
            const requstOption = {
                method: options.method,
                url: options.href,
                headers: _headers,
                data: body
            };
            return client._doRequest(requstOption, outputStream);
        });
    }

    private async _doRequest(options: AxiosRequestConfig, outputStream: boolean | stream.Writable): Promise<any> {
        if (outputStream) {
            return this.establishSSEConnection(options);
        }
        try {
            const response: AxiosResponse = await this.axiosInstance.request(options);
            // 处理响应体
            return this._recvResponse(response as any);
        }
        catch (error) {
            throw error;
        }

    }

    public async establishSSEConnection(options: AxiosRequestConfig): Promise<AsyncIterable<any>> {
        const {url, headers, data} = options;
        try {
            const sseStream: AsyncIterable<any> = Stream.fromSSEResponse(await fetch(url, {
                method: 'POST',
                headers: headers as any,
                body: data
            }), this.controller) as any;
            return sseStream;
        }
        catch (error) {
            // Handle errors
            console.error('Error establishing SSE connection:', error.message);
            throw error;
        }
    }

    // New method for handling SSE line

    private _recvResponse(response: AxiosResponse): any {
        const statusCode = response.status;
        const responseBody = response.data;
        if (statusCode >= 100 && statusCode < 200) {
            throw this.failure(statusCode, 'Can not handle 1xx http status code.');
        }
        else if (statusCode < 100 || statusCode >= 300) {
            throw this.failure(statusCode, responseBody.message);
        }
        return response;
    }

    private failure(statusCode: number, message: string | Buffer): any {
        const response: Record<string, any> = {};
        response[H.X_STATUS_CODE] = statusCode;
        response[H.X_MESSAGE] = Buffer.isBuffer(message) ? message.toString() : message;
        return response;
    }

    private setAuthorizationHeader(
        signFunction: ((credentials: any, method: any, path: any, headers: any) => [string, string] | string) | undefined,
        headers: Record<string, any>,
        options: http.RequestOptions
    ): Q.Promise<any> {
        const client = this;
        if (typeof signFunction === 'function') {
            const promise = signFunction(this.config.credentials, options.method!, options.path!, options.headers!);
            if (this.isPromise(promise)) {
                return promise.then(([authorization, xbceDate]: [string, string]) => {
                    headers[H.AUTHORIZATION] = authorization;
                    if (xbceDate) {
                        headers[H.X_BCE_DATE] = xbceDate;
                    }
                });
            }
            else if (typeof promise === 'string') {
                headers[H.AUTHORIZATION] = promise;
            }
            else {
                throw new Error(`Invalid signature = (${promise})`);
            }
        }
        else {
            headers[H.AUTHORIZATION] = this.createSignature(
                this.config.credentials,
                options.method!,
                options.path!,
                options.headers!
            );
        }

        return Q.resolve(); // Return a resolved promise for consistency
    }

    private _getRequestUrl(path: string, params: Record<string, any>): string {
        let uri = path;
        const qs = this.buildQueryString(params);
        if (qs) {
            uri += '?' + qs;
        }

        if (/^https?/.test(uri)) {
            return uri;
        }

        return this.config.endpoint + uri;
    }

    private buildQueryString(params: Record<string, any>): string {
        const urlEncodeStr = require('querystring').stringify(params);

        // https://en.wikipedia.org/wiki/Percent-encoding
        return urlEncodeStr.replace(/[()'!~.*\-_]/g, (char : any) => {
            return '%' + char.charCodeAt(0).toString(16);
        });
    }

    /**
     * 猜测数据长度
     *
     * @param data 数据，可以是字符串、Buffer、可读流
     * @returns 返回数据长度
     * @throws {Error} 当没有指定 Content-Length 时抛出异常
     */
    private _guessContentLength(data: string | Buffer | stream.Readable): number {
        if (data == null) {
            return 0;
        }
        else if (typeof data === 'string') {
            return Buffer.byteLength(data);
        }
        else if (typeof data === 'object') {
            if (data instanceof Blob) {
                return data.size;
            }
            if (data instanceof ArrayBuffer) {
                return data.byteLength;
            }
            if (Buffer.isBuffer(data)) {
                return data.length;
            }
            if (typeof data === 'object') {
                const keys = Object.keys(data);
                return keys.length;
            }
        }
        else if (Buffer.isBuffer(data)) {
            return (data as any).length;
        }

        throw new Error('No Content-Length is specified.');
    }


    private isPromise(obj: any): obj is Q.Promise<any> {
        return obj && (typeof obj === 'object' || typeof obj === 'function') && typeof obj.then === 'function';
    }

    private createSignature(credentials: any, httpMethod: string, path: string, headers: Record<string, any>): string {
        const auth = new Auth(credentials.ak, credentials.sk);
        return auth.generateAuthorization(httpMethod, path, {}, headers);
    }
}

export default HttpClient;