import packageJson from '../../package.json';
import Fetch, {FetchConfig} from '../Fetch/index';
import Auth from './auth';
import * as H from './headers';
import {urlObjectToPlainObject} from './strings';
import {getCurrentEnvironment} from '../utils';

let URLClass;
if (getCurrentEnvironment() === 'browser') {
    URLClass = window.URL.bind(window);
}
else {
    URLClass = require('url').URL;
}

// 获取版本号
const version = packageJson.version;

class HttpClient {
    private fetchInstance;
    private readonly defaultHeaders: Record<string, any> = {
        [H.CONTENT_TYPE]: 'application/json; charset=UTF-8',
        [H.USER_AGENT]:
            typeof navigator !== 'undefined' && navigator.userAgent
                ? navigator.userAgent
                : `bce-sdk-nodejs/${version}/unknown/unknown`,
        [H.X_BCE_DATE]: new Date().toISOString().replace(/\.\d+Z$/, 'Z'),
    };

    constructor(
        private config: any,
        fetchConfig?: FetchConfig
    ) {
        this.fetchInstance = new Fetch(fetchConfig);
    }

    /**
     * 获取签名
     *
     * @param config 请求配置对象
     * @returns 返回包含签名信息的 fetchOptions 对象
     */
    async getSignature(config): Promise<any> {
        const {httpMethod, path, body, headers, params, signFunction} = config;
        const method = httpMethod.toUpperCase();
        const requestUrl = this._getRequestUrl(path);
        const _headers = Object.assign({}, this.defaultHeaders, headers);
        if (!_headers.hasOwnProperty(H.CONTENT_LENGTH)) {
            let contentLength = this._guessContentLength(body);
            if (!(contentLength === 0 && /GET|HEAD/i.test(method))) {
                _headers[H.CONTENT_LENGTH] = contentLength;
            }
        }
        const url = new URLClass(requestUrl) as any;
        _headers[H.HOST] = url.host;
        const options = urlObjectToPlainObject(url, method, _headers);
        const reqHeaders = await this.setAuthorizationHeader(signFunction, _headers, options, params);
        const fetchOptions = {
            url: options.href,
            method: options.method,
            headers: reqHeaders,
            body,
        };
        return fetchOptions;
    }

    private async setAuthorizationHeader(
        signFunction:
            | ((credentials: any, method: any, path: any, headers: any) => [string, string] | string)
            | undefined,
        headers: Record<string, any>,
        options: any,
        params: Record<string, any>
    ): Promise<Record<string, any>> {
        if (typeof signFunction === 'function') {
            const result = signFunction(this.config.credentials, options.method!, options.path!, headers);
            if (result instanceof Promise) {
                const [authorization, xbceDate] = await result;
                headers[H.AUTHORIZATION] = authorization;
                if (xbceDate) {
                    headers[H.X_BCE_DATE] = xbceDate;
                }
            }
            else if (typeof result === 'string') {
                headers[H.AUTHORIZATION] = result;
            }
            else {
                throw new Error(`Invalid signature = (${result})`);
            }
        }
        else {
            headers[H.AUTHORIZATION] = this.createSignature(
                this.config.credentials,
                options.method!,
                options.path!,
                headers,
                params
            );
        }
        return headers;
    }

    private _getRequestUrl(path: string, params?: Record<string, any>): string {
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
        const urlSearchParams = new URLSearchParams(params);
        return urlSearchParams.toString();
    }

    /**
     * 猜测数据长度
     *
     * @param data 数据，可以是字符串、Buffer、可读流
     * @returns 返回数据长度
     * @throws {Error} 当没有指定 Content-Length 时抛出异常
     */
    private _guessContentLength(data: string | Buffer | Blob | ArrayBuffer | any): number {
        if (data == null) {
            return 0;
        }
        else if (typeof data === 'string') {
            return new TextEncoder().encode(data).length;
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

        throw new Error('No Content-Length is specified.');
    }

    private createSignature(
        credentials: any,
        httpMethod: string,
        path: string,
        headers?: Record<string, any>,
        params?: Record<string, any>
    ): string {
        const auth = new Auth(credentials.ak, credentials.sk);
        return auth.generateAuthorization(httpMethod, path, params, headers);
    }
}

export default HttpClient;
