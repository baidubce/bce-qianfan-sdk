(function (global, factory) {
    typeof exports === 'object' && typeof module !== 'undefined' ? factory(exports, require('axios'), require('process'), require('events'), require('underscore'), require('q'), require('url'), require('debug'), require('util'), require('crypto')) :
    typeof define === 'function' && define.amd ? define(['exports', 'axios', 'process', 'events', 'underscore', 'q', 'url', 'debug', 'util', 'crypto'], factory) :
    (global = typeof globalThis !== 'undefined' ? globalThis : global || self, factory(global.MyLibrary = {}, global.axios, global.process, global.events, global._, global.Q, global.url, global.createDebug, global.util, global.crypto));
})(this, (function (exports, axios, process, events, _, Q, url, createDebug, util, crypto) { 'use strict';

    function _interopNamespaceDefault(e) {
        var n = Object.create(null);
        if (e) {
            Object.keys(e).forEach(function (k) {
                if (k !== 'default') {
                    var d = Object.getOwnPropertyDescriptor(e, k);
                    Object.defineProperty(n, k, d.get ? d : {
                        enumerable: true,
                        get: function () { return e[k]; }
                    });
                }
            });
        }
        n.default = e;
        return Object.freeze(n);
    }

    var process__namespace = /*#__PURE__*/_interopNamespaceDefault(process);
    var ___namespace = /*#__PURE__*/_interopNamespaceDefault(_);
    var Q__namespace = /*#__PURE__*/_interopNamespaceDefault(Q);
    var util__namespace = /*#__PURE__*/_interopNamespaceDefault(util);
    var crypto__namespace = /*#__PURE__*/_interopNamespaceDefault(crypto);

    var version$1 = "0.0.0";

    const CONTENT_TYPE = 'Content-Type';
    const CONTENT_LENGTH = 'Content-Length';
    const CONTENT_MD5 = 'Content-MD5';
    const CONNECTION = 'Connection';
    const HOST = 'Host';
    const USER_AGENT = 'User-Agent';
    /** BOS 相关headers */
    const AUTHORIZATION = 'Authorization';
    const X_BCE_DATE = 'x-bce-date';
    const X_STATUS_CODE = 'status_code';
    const X_MESSAGE = 'message';

    const kEscapedMap = {
        '!': '%21',
        '\'': '%27',
        '(': '%28',
        ')': '%29',
        '*': '%2A'
    };
    function normalize(string, encodingSlash) {
        let result = encodeURIComponent(string);
        result = result.replace(/[!'\(\)\*]/g, ($1) => kEscapedMap[$1]);
        if (encodingSlash === false) {
            result = result.replace(/%2F/gi, '/');
        }
        return result;
    }
    function trim(string) {
        return (string || '').replace(/^\s+|\s+$/g, '');
    }
    function urlObjectToPlainObject(url, httpMethod, headers) {
        return {
            protocol: url.protocol,
            auth: url.username || (url.password ? '****:' : '') + url.password,
            host: url.host,
            port: url.port,
            hostname: url.hostname,
            hash: url.hash,
            search: url.search,
            query: url.searchParams.toString(),
            pathname: url.pathname,
            path: url.pathname + url.search,
            href: url.href,
            method: httpMethod,
            headers: headers
        };
    }

    const debug$1 = createDebug('bce-sdk:Auth');
    class Auth {
        constructor(ak, sk) {
            this.ak = ak;
            this.sk = sk;
        }
        generateAuthorization(method, resource, params, headers, timestamp, expirationInSeconds, headersToSign) {
            const now = this.getTimestamp(timestamp);
            const rawSessionKey = util__namespace.format('bce-auth-v1/%s/%s/%d', this.ak, now, expirationInSeconds || 1800);
            debug$1('rawSessionKey = %j', rawSessionKey);
            const sessionKey = this.hash(rawSessionKey, this.sk);
            const canonicalUri = this.generateCanonicalUri(resource);
            const canonicalQueryString = this.queryStringCanonicalization(params || {});
            const rv = this.headersCanonicalization(headers || {}, headersToSign);
            const canonicalHeaders = rv[0];
            const signedHeaders = rv[1];
            debug$1('canonicalUri = %j', canonicalUri);
            debug$1('canonicalQueryString = %j', canonicalQueryString);
            debug$1('canonicalHeaders = %j', canonicalHeaders);
            debug$1('signedHeaders = %j', signedHeaders);
            const rawSignature = util__namespace.format('%s\n%s\n%s\n%s', method, canonicalUri, canonicalQueryString, canonicalHeaders);
            debug$1('rawSignature = %j', rawSignature);
            debug$1('sessionKey = %j', sessionKey);
            const signature = this.hash(rawSignature, sessionKey);
            if (signedHeaders.length) {
                return util__namespace.format('%s/%s/%s', rawSessionKey, signedHeaders.join(';'), signature);
            }
            return util__namespace.format('%s//%s', rawSessionKey, signature);
        }
        normalize(string, encodingSlash = true) {
            const kEscapedMap = {
                '!': '%21',
                "'": '%27',
                '(': '%28',
                ')': '%29',
                '*': '%2A'
            };
            if (string === null) {
                return '';
            }
            let result = encodeURIComponent(string);
            result = result.replace(/[!'\(\)\*]/g, ($1) => {
                return kEscapedMap[$1];
            });
            if (!encodingSlash) {
                result = result.replace(/%2F/gi, '/');
            }
            return result;
        }
        getTimestamp(timestamp) {
            const now = timestamp ? new Date(timestamp * 1000) : new Date();
            return now.toISOString().replace(/\.\d+Z$/, 'Z');
        }
        generateCanonicalUri(url) {
            if (!url?.includes('bos-share.baidubce.com')) {
                return url;
            }
            const urlObj = new URL(url);
            const pathname = urlObj.pathname.trim();
            const resources = pathname.replace(/^\//, '').split('/');
            if (!resources) {
                return '';
            }
            let normalizedResourceStr = '';
            for (let i = 0; i < resources.length; i++) {
                normalizedResourceStr += '/' + this.normalize(resources[i]);
            }
            return normalizedResourceStr;
        }
        queryStringCanonicalization(params) {
            const canonicalQueryString = [];
            Object.keys(params).forEach((key) => {
                if (key.toLowerCase() === AUTHORIZATION.toLowerCase()) {
                    return;
                }
                const value = params[key] == null ? '' : params[key];
                canonicalQueryString.push(`${key}=${this.normalize(value)}`);
            });
            canonicalQueryString.sort();
            return canonicalQueryString.join('&');
        }
        headersCanonicalization(headers, headersToSign) {
            if (!headersToSign || !headersToSign.length) {
                headersToSign = [HOST, CONTENT_MD5, CONTENT_LENGTH, CONTENT_TYPE];
            }
            debug$1('headers = %j, headersToSign = %j', headers, headersToSign);
            const headersMap = {};
            headersToSign.forEach((item) => {
                headersMap[item.toLowerCase()] = true;
            });
            const canonicalHeaders = [];
            Object.keys(headers).forEach((key) => {
                let value = headers[key];
                value = _.isString(value) ? trim(value) : value;
                if (value == null || value === '') {
                    return;
                }
                key = key.toLowerCase();
                if (/^x\-bce\-/.test(key) || headersMap[key] === true) {
                    canonicalHeaders.push(util__namespace.format('%s:%s', normalize(key), normalize(value)));
                }
            });
            canonicalHeaders.sort();
            const signedHeaders = [];
            canonicalHeaders.forEach((item) => {
                signedHeaders.push(item.split(':')[0]);
            });
            return [canonicalHeaders.join('\n'), signedHeaders];
        }
        hash(data, key) {
            const sha256Hmac = crypto__namespace.createHmac('sha256', key);
            sha256Hmac.update(data);
            return sha256Hmac.digest('hex');
        }
    }

    const debug = createDebug('bce-sdk:HttpClient');
    // 获取版本号
    const version = version$1;
    class HttpClient extends events.EventEmitter {
        constructor(config) {
            super();
            this.config = config;
            this.defaultHeaders = {
                [CONNECTION]: 'close',
                [CONTENT_TYPE]: 'application/json; charset=UTF-8',
                // 检查是否在浏览器环境中
                [USER_AGENT]: typeof navigator !== 'undefined' && navigator.userAgent
                    ? navigator.userAgent
                    : `bce-sdk-nodejs/${version}/${process__namespace.platform}/${process__namespace.version}`,
                [X_BCE_DATE]: new Date().toISOString().replace(/\.\d+Z$/, 'Z')
            };
            this.axiosInstance = axios.create();
        }
        sendRequest(httpMethod, path, body, headers, params, signFunction, outputStream) {
            httpMethod = httpMethod.toUpperCase();
            const requestUrl = this._getRequestUrl(path, params);
            const _headers = ___namespace.extend({}, this.defaultHeaders, headers);
            if (!_headers.hasOwnProperty(CONTENT_LENGTH)) {
                var contentLength = this._guessContentLength(body);
                if (!(contentLength === 0 && /GET|HEAD/i.test(httpMethod))) {
                    // 如果是 GET 或 HEAD 请求，并且 Content-Length 是 0，那么 Request Header 里面就不要出现 Content-Length
                    // 否则本地计算签名的时候会计算进去，但是浏览器发请求的时候不一定会有，此时导致 Signature Mismatch 的情况
                    _headers[CONTENT_LENGTH] = contentLength;
                }
            }
            const client = this;
            const url$1 = new url.URL(requestUrl);
            _headers[HOST] = url$1.host;
            const options = urlObjectToPlainObject(url$1, httpMethod, _headers);
            return this.setAuthorizationHeader(signFunction, _headers, options).then(() => {
                debug('options = %j', options);
                const requstOption = {
                    method: options.method,
                    url: options.href,
                    headers: _headers,
                    data: body
                };
                return client._doRequest(requstOption);
            });
        }
        async _doRequest(options) {
            try {
                const response = await this.axiosInstance.request(options);
                // 处理响应体
                return this._recvResponse(response);
            }
            catch (error) {
                throw error;
            }
        }
        _recvResponse(response) {
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
        failure(statusCode, message) {
            const response = {};
            response[X_STATUS_CODE] = statusCode;
            response[X_MESSAGE] = Buffer.isBuffer(message) ? message.toString() : message;
            return response;
        }
        setAuthorizationHeader(signFunction, headers, options) {
            if (typeof signFunction === 'function') {
                const promise = signFunction(this.config.credentials, options.method, options.path, options.headers);
                if (this.isPromise(promise)) {
                    return promise.then(([authorization, xbceDate]) => {
                        headers[AUTHORIZATION] = authorization;
                        if (xbceDate) {
                            headers[X_BCE_DATE] = xbceDate;
                        }
                    });
                }
                else if (typeof promise === 'string') {
                    headers[AUTHORIZATION] = promise;
                }
                else {
                    throw new Error(`Invalid signature = (${promise})`);
                }
            }
            else {
                headers[AUTHORIZATION] = this.createSignature(this.config.credentials, options.method, options.path, options.headers);
            }
            return Q__namespace.resolve(); // Return a resolved promise for consistency
        }
        _getRequestUrl(path, params) {
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
        buildQueryString(params) {
            const urlEncodeStr = require('querystring').stringify(params);
            // https://en.wikipedia.org/wiki/Percent-encoding
            return urlEncodeStr.replace(/[()'!~.*\-_]/g, (char) => {
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
        _guessContentLength(data) {
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
                return data.length;
            }
            throw new Error('No Content-Length is specified.');
        }
        isPromise(obj) {
            return obj && (typeof obj === 'object' || typeof obj === 'function') && typeof obj.then === 'function';
        }
        createSignature(credentials, httpMethod, path, headers) {
            const auth = new Auth(credentials.ak, credentials.sk);
            return auth.generateAuthorization(httpMethod, path, {}, headers);
        }
    }

    const modelInfoMap$2 = {
        "ERNIE-Bot-turbo": {
            endpoint: "/chat/eb-instant",
            required_keys: ["messages"],
            optional_keys: [
                "stream",
                "temperature",
                "top_p",
                "penalty_score",
                "user_id",
                "tools",
                "tool_choice",
                "system",
            ],
        },
        "ERNIE-Bot": {
            endpoint: "/chat/completions",
            required_keys: ["messages"],
            optional_keys: [
                "stream",
                "temperature",
                "top_p",
                "penalty_score",
                "functions",
                "system",
                "user_id",
                "user_setting",
                "stop",
                "disable_search",
                "enable_citation",
                "max_output_tokens",
                "tool_choice",
            ],
        },
        "ERNIE-Bot-4": {
            endpoint: "/chat/completions_pro",
            required_keys: ["messages"],
            optional_keys: [
                "stream",
                "temperature",
                "top_p",
                "penalty_score",
                "functions",
                "system",
                "user_id",
                "stop",
                "disable_search",
                "enable_citation",
                "max_output_tokens",
            ],
        },
        "ERNIE-Bot-8k": {
            endpoint: "/chat/ernie_bot_8k",
            required_keys: ["messages"],
            optional_keys: [
                "functions",
                "temperature",
                "top_p",
                "penalty_score",
                "stream",
                "system",
                "stop",
                "disable_search",
                "enable_citation",
                "user_id",
            ],
        },
        "ERNIE-Speed": {
            endpoint: "/chat/eb_turbo_pro",
            required_keys: ["messages"],
            optional_keys: [
                "stream",
                "temperature",
                "top_p",
                "penalty_score",
                "user_id",
                "tools",
                "tool_choice",
                "system",
            ],
        },
        "ERNIE-Bot-turbo-AI": {
            endpoint: "/chat/ai_apaas",
            required_keys: ["messages"],
            optional_keys: [
                "stream",
                "temperature",
                "top_p",
                "penalty_score",
                "system",
                "user_id",
                "tools",
                "tool_choice",
            ],
        },
        "EB-turbo-AppBuilder": {
            endpoint: "/chat/ai_apaas",
            required_keys: ["messages"],
            optional_keys: [
                "stream",
                "temperature",
                "top_p",
                "penalty_score",
                "system",
                "user_id",
                "tools",
                "tool_choice",
            ],
        },
        "BLOOMZ-7B": {
            endpoint: "/chat/bloomz_7b1",
            required_keys: ["messages"],
            optional_keys: [
                "stream",
                "user_id",
                "temperature",
                "top_k",
                "top_p",
                "penalty_score",
                "stop",
                "tools",
                "tool_choice",
            ],
        },
        "Llama-2-7b-chat": {
            endpoint: "/chat/llama_2_7b",
            required_keys: ["messages"],
            optional_keys: [
                "stream",
                "user_id",
                "temperature",
                "top_k",
                "top_p",
                "penalty_score",
                "stop",
                "tools",
                "tool_choice",
            ],
        },
        "Llama-2-13b-chat": {
            endpoint: "/chat/llama_2_13b",
            required_keys: ["messages"],
            optional_keys: [
                "stream",
                "user_id",
                "temperature",
                "top_k",
                "top_p",
                "penalty_score",
                "stop",
                "tools",
                "tool_choice",
            ],
        },
        "Llama-2-70b-chat": {
            endpoint: "/chat/llama_2_70b",
            required_keys: ["messages"],
            optional_keys: [
                "stream",
                "user_id",
                "temperature",
                "top_k",
                "top_p",
                "penalty_score",
                "stop",
                "tools",
                "tool_choice",
            ],
        },
        "Qianfan-BLOOMZ-7B-compressed": {
            endpoint: "/chat/qianfan_bloomz_7b_compressed",
            required_keys: ["messages"],
            optional_keys: [
                "stream",
                "user_id",
                "temperature",
                "top_k",
                "top_p",
                "penalty_score",
                "stop",
                "tools",
                "tool_choice",
            ],
        },
        "Qianfan-Chinese-Llama-2-7B": {
            endpoint: "/chat/qianfan_chinese_llama_2_7b",
            required_keys: ["messages"],
            optional_keys: [
                "stream",
                "user_id",
                "temperature",
                "top_k",
                "top_p",
                "penalty_score",
                "stop",
                "tools",
                "tool_choice",
            ],
        },
        "ChatGLM2-6B-32K": {
            endpoint: "/chat/chatglm2_6b_32k",
            required_keys: ["messages"],
            optional_keys: [
                "stream",
                "user_id",
                "temperature",
                "top_k",
                "top_p",
                "penalty_score",
                "stop",
                "tools",
                "tool_choice",
            ],
        },
        "AquilaChat-7B": {
            endpoint: "/chat/aquilachat_7b",
            required_keys: ["messages"],
            optional_keys: [
                "stream",
                "user_id",
                "temperature",
                "top_k",
                "top_p",
                "penalty_score",
                "stop",
                "tools",
                "tool_choice",
            ],
        },
        "XuanYuan-70B-Chat-4bit": {
            endpoint: "/chat/xuanyuan_70b_chat",
            required_keys: ["messages"],
            optional_keys: [
                "stream",
                "user_id",
                "temperature",
                "top_k",
                "top_p",
                "penalty_score",
                "stop",
                "tools",
                "tool_choice",
            ],
        },
        "Qianfan-Chinese-Llama-2-13B": {
            endpoint: "/chat/qianfan_chinese_llama_2_13b",
            required_keys: ["messages"],
            optional_keys: [
                "stream",
                "user_id",
                "temperature",
                "top_k",
                "top_p",
                "penalty_score",
                "stop",
                "tools",
                "tool_choice",
            ],
        },
        "ChatLaw": {
            endpoint: "/chat/chatlaw",
            required_keys: ["messages", "extra_parameters"],
            optional_keys: [
                "stream",
                "user_id",
                "temperature",
                "top_p",
                "tools",
                "tool_choice",
            ],
        },
        "Yi-34B-Chat": {
            endpoint: "/chat/yi_34b_chat",
            required_keys: ["messages"],
            optional_keys: [
                "stream",
                "user_id",
                "temperature",
                "top_k",
                "top_p",
                "penalty_score",
                "stop",
                "tools",
                "tool_choice",
            ],
        },
        UNSPECIFIED_MODEL: {
            endpoint: "",
            required_keys: ["messages"],
            optional_keys: [],
        },
    };

    const base_host = 'https://aip.baidubce.com';
    const base_path = '/rpc/2.0/ai_custom/v1/wenxinworkshop';
    const api_base = base_host + base_path;
    const DEFAULT_HEADERS = {
        'Content-Type': 'application/json',
        Accept: 'application/json',
    };

    /**
     * 使用 AK，SK 生成鉴权签名（Access Token）
     * @return string 鉴权签名信息（Access Token）
     */
    async function getAccessToken(API_KEY, SECRET_KEY, headers) {
        const url = `https://aip.baidubce.com/oauth/2.0/token?grant_type=client_credentials&client_id=${API_KEY}&client_secret=${SECRET_KEY}`;
        const resp = await axios.post(url, {}, { headers, withCredentials: false });
        if (resp.data?.error && resp.data?.error_description) {
            throw new Error(resp.data.error_description);
        }
        const expires_in = resp.data.expires_in + Date.now() / 1000;
        return {
            access_token: resp.data.access_token,
            expires_in,
        };
    }
    function getIAMConfig(ak, sk) {
        return {
            credentials: {
                ak,
                sk,
            },
            endpoint: base_host,
        };
    }
    /**
     * 获取请求体
     *
     * @param body 聊天体
     * @param version 版本号
     * @returns 返回JSON格式的字符串
     */
    function getRequestBody(body, version) {
        // 埋点信息
        body.extra_parameters = {
            ...body.extra_parameters,
            'request_source': `qianfan_js_sdk_v${version}`,
        };
        return JSON.stringify(body);
    }
    /**
     * 获取模型对应的API端点
     * @param model 模型实例
     * @param modelInfoMap 模型信息映射表
     * @returns 返回模型对应的API端点
     * @throws 当模型信息或API端点不存在时抛出异常
     */
    function getModelEndpoint(model, modelInfoMap) {
        const modelInfo = modelInfoMap[model];
        if (!modelInfo) {
            throw new Error(`Model info not found for model: ${model}`);
        }
        const endpoint = modelInfo.endpoint;
        if (!endpoint) {
            throw new Error(`Endpoint not found for model: ${model}`);
        }
        return endpoint;
    }
    /*
     * 获取请求路径
    */
    const getPath = (model, modelInfoMap, Authentication, endpoint = '', type) => {
        let path;
        if (model && modelInfoMap[model]) {
            const _endpoint = getModelEndpoint(model, modelInfoMap);
            path = Authentication === 'IAM' ? `${base_path}${_endpoint}` : `${api_base}${_endpoint}`;
        }
        else if (endpoint && type) {
            path = Authentication === 'IAM' ? `${base_path}/${type}/${endpoint}` : `${api_base}/${type}/${endpoint}`;
        }
        else {
            throw new Error('Path not found');
        }
        return path;
    };

    class ChatCompletion {
        /**
         * 千帆大模型
         * @param API_KEY API Key，IAM、AK/SK 鉴权时必填
         * @param SECRET_KEY Secret Key，IAM、AK/SK 鉴权时必填
         * @param Type 鉴权方式，默认IAM鉴权，如果使用AK/SK鉴权，请设置为'AK'
         */
        constructor(API_KEY, SECRET_KEY, Type = 'IAM') {
            this.Type = 'IAM';
            this.headers = DEFAULT_HEADERS;
            this.access_token = '';
            this.expires_in = 0;
            this.API_KEY = API_KEY;
            this.SECRET_KEY = SECRET_KEY;
            this.Type = Type;
            this.axiosInstance = axios.create();
        }
        async sendRequest(model, body, stream = false) {
            const endpoint = getModelEndpoint(model, modelInfoMap$2);
            const requestBody = getRequestBody(body, version$1);
            // IAM鉴权
            if (this.Type === 'IAM') {
                const config = getIAMConfig(this.API_KEY, this.SECRET_KEY);
                const client = new HttpClient(config);
                const path = `${base_path}${endpoint}`;
                const response = await client.sendRequest('POST', path, requestBody, this.headers);
                return response;
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
                };
                try {
                    const resp = await this.axiosInstance.request(options);
                    return resp.data;
                }
                catch (error) {
                    throw new Error(error);
                }
                // }
            }
            // TODO 流式结果处理
            throw new Error(`Unsupported authentication type: ${this.Type}`);
        }
        async chat(body, model = 'ERNIE-Bot-turbo') {
            const stream = body.stream ?? false;
            return this.sendRequest(model, body, stream);
        }
    }

    const modelInfoMap$1 = {
        "ERNIE-Bot-turbo": {
            endpoint: "/chat/eb-instant",
            required_keys: ["messages"],
            optional_keys: [
                "stream",
                "temperature",
                "top_p",
                "penalty_score",
                "user_id",
                "tools",
                "tool_choice",
                "system"
            ]
        },
        "ERNIE-Bot": {
            endpoint: "/chat/completions",
            required_keys: ["messages"],
            optional_keys: [
                "stream",
                "temperature",
                "top_p",
                "penalty_score",
                "user_id",
                "system",
                "stop",
                "disable_search",
                "enable_citation",
                "max_output_tokens",
            ],
        },
        "ERNIE-Bot-4": {
            endpoint: "/chat/completions_pro",
            required_keys: ["messages"],
            optional_keys: [
                "stream",
                "temperature",
                "top_p",
                "penalty_score",
                "user_id",
                "system",
                "stop",
                "disable_search",
                "enable_citation",
                "max_output_tokens",
            ],
        },
        "ERNIE-Bot-8k": {
            endpoint: "/chat/ernie_bot_8k",
            required_keys: ["messages"],
            optional_keys: [
                "functions",
                "temperature",
                "top_p",
                "penalty_score",
                "stream",
                "system",
                "stop",
                "disable_search",
                "enable_citation",
                "user_id",
            ],
        },
        "ERNIE-Speed": {
            endpoint: "/chat/eb_turbo_pro",
            required_keys: ["messages"],
            optional_keys: [
                "stream",
                "temperature",
                "top_p",
                "penalty_score",
                "user_id",
                "tools",
                "tool_choice",
                "system",
            ],
        },
        "EB-turbo-AppBuilder": {
            endpoint: "/chat/ai_apaas",
            required_keys: ["messages"],
            optional_keys: [
                "stream",
                "temperature",
                "top_p",
                "penalty_score",
                "system",
                "user_id",
                "tools",
                "tool_choice",
            ],
        },
        "BLOOMZ-7B": {
            endpoint: "/chat/bloomz_7b1",
            required_keys: ["messages"],
            optional_keys: [
                "stream",
                "user_id",
                "temperature",
                "top_k",
                "top_p",
                "penalty_score",
                "stop",
                "tools",
                "tool_choice",
            ],
        },
        "Llama-2-7b-chat": {
            endpoint: "/chat/llama_2_7b",
            required_keys: ["messages"],
            optional_keys: [
                "stream",
                "user_id",
                "temperature",
                "top_k",
                "top_p",
                "penalty_score",
                "stop",
                "tools",
                "tool_choice",
            ],
        },
        "Llama-2-13b-chat": {
            endpoint: "/chat/llama_2_13b",
            required_keys: ["messages"],
            optional_keys: [
                "stream",
                "user_id",
                "temperature",
                "top_k",
                "top_p",
                "penalty_score",
                "stop",
                "tools",
                "tool_choice",
            ],
        },
        "Llama-2-70b-chat": {
            endpoint: "/chat/llama_2_70b",
            required_keys: ["messages"],
            optional_keys: [
                "stream",
                "user_id",
                "temperature",
                "top_k",
                "top_p",
                "penalty_score",
                "stop",
                "tools",
                "tool_choice",
            ],
        },
        "Qianfan-BLOOMZ-7B-compressed": {
            endpoint: "/chat/qianfan_bloomz_7b_compressed",
            required_keys: ["messages"],
            optional_keys: [
                "stream",
                "user_id",
                "temperature",
                "top_k",
                "top_p",
                "penalty_score",
                "stop",
                "tools",
                "tool_choice",
            ],
        },
        "Qianfan-Chinese-Llama-2-7B": {
            endpoint: "/chat/qianfan_chinese_llama_2_7b",
            required_keys: ["messages"],
            optional_keys: [
                "stream",
                "user_id",
                "temperature",
                "top_k",
                "top_p",
                "penalty_score",
                "stop",
                "tools",
                "tool_choice",
            ],
        },
        "ChatGLM2-6B-32K": {
            endpoint: "/chat/chatglm2_6b_32k",
            required_keys: ["messages"],
            optional_keys: [
                "stream",
                "user_id",
                "temperature",
                "top_k",
                "top_p",
                "penalty_score",
                "stop",
                "tools",
                "tool_choice",
            ],
        },
        "AquilaChat-7B": {
            endpoint: "/chat/aquilachat_7b",
            required_keys: ["messages"],
            optional_keys: [
                "stream",
                "user_id",
                "temperature",
                "top_k",
                "top_p",
                "penalty_score",
                "stop",
                "tools",
                "tool_choice",
            ],
        },
        "XuanYuan-70B-Chat-4bit": {
            endpoint: "/chat/xuanyuan_70b_chat",
            required_keys: ["messages"],
            optional_keys: [
                "stream",
                "user_id",
                "temperature",
                "top_k",
                "top_p",
                "penalty_score",
                "stop",
                "tools",
                "tool_choice",
            ],
        },
        "Qianfan-Chinese-Llama-2-13B": {
            endpoint: "/chat/qianfan_chinese_llama_2_13b",
            required_keys: ["messages"],
            optional_keys: [
                "stream",
                "user_id",
                "temperature",
                "top_k",
                "top_p",
                "penalty_score",
                "stop",
                "tools",
                "tool_choice",
            ],
        },
        "ChatLaw": {
            endpoint: "/chat/chatlaw",
            required_keys: ["messages", "extra_parameters"],
            optional_keys: [
                "stream",
                "user_id",
                "temperature",
                "top_p",
                "tools",
                "tool_choice",
            ],
        },
        "SQLCoder-7B": {
            endpoint: "/completions/sqlcoder_7b",
            required_keys: ["prompt"],
            optional_keys: [
                "stream",
                "user_id",
                "temperature",
                "top_k",
                "top_p",
                "penalty_score",
                "stop",
                "tools",
                "tool_choice",
            ],
        },
        "CodeLlama-7b-Instruct": {
            endpoint: "/completions/codellama_7b_instruct",
            required_keys: ["prompt"],
            optional_keys: [
                "stream",
                "user_id",
                "temperature",
                "top_k",
                "top_p",
                "penalty_score",
                "stop",
                "tools",
                "tool_choice",
            ],
        },
        "Yi-34B-Chat": {
            endpoint: "/chat/yi_34b_chat",
            required_keys: ["messages"],
            optional_keys: [
                "stream",
                "user_id",
                "temperature",
                "top_k",
                "top_p",
                "penalty_score",
                "stop",
                "tools",
                "tool_choice",
            ],
        },
        UNSPECIFIED_MODEL: {
            endpoint: '',
            required_keys: ['prompt'],
            optional_keys: []
        },
    };

    class Completions {
        /**
         * 千帆大模型
         * @param API_KEY API Key，IAM、AK/SK 鉴权时必填
         * @param SECRET_KEY Secret Key，IAM、AK/SK 鉴权时必填
         * @param Type 鉴权方式，默认IAM鉴权，如果使用AK/SK鉴权，请设置为'AK'
         * @param Endpoint 请求地址，默认使用千帆大模型服务
         */
        constructor(API_KEY, SECRET_KEY, Type = 'IAM', Endpoint = '') {
            this.Type = 'IAM';
            this.Endpoint = '';
            this.headers = DEFAULT_HEADERS;
            this.access_token = '';
            this.expires_in = 0;
            this.API_KEY = API_KEY;
            this.SECRET_KEY = SECRET_KEY;
            this.Type = Type;
            this.Endpoint = Endpoint;
            this.axiosInstance = axios.create();
        }
        async sendRequest(model, body, stream = false, endpoint) {
            const path = getPath(model, modelInfoMap$1, endpoint, 'completions');
            const requestBody = getRequestBody(body, version$1);
            // IAM鉴权
            if (this.Type === 'IAM') {
                const config = getIAMConfig(this.API_KEY, this.SECRET_KEY);
                const client = new HttpClient(config);
                const response = await client.sendRequest('POST', path, requestBody, this.headers);
                return response;
            }
            // AK/SK鉴权    
            if (this.Type === 'AK') {
                const access = await getAccessToken(this.API_KEY, this.SECRET_KEY, this.headers);
                // 重试问题初始化进入不了 TODO!!
                // if (access.expires_in < Date.now() / 1000) { 
                const url = `${path}?access_token=${access.access_token}`;
                const options = {
                    method: 'POST',
                    url: url,
                    headers: this.headers,
                    data: requestBody
                };
                try {
                    const resp = await this.axiosInstance.request(options);
                    return resp.data;
                }
                catch (error) {
                    throw new Error(error);
                }
                // }
            }
            // TODO 流式结果处理
            throw new Error(`Unsupported authentication type: ${this.Type}`);
        }
        async completions(body, model = 'ERNIE-Bot-turbo') {
            const stream = body.stream ?? false;
            return this.sendRequest(model, body, stream, this.Endpoint);
        }
    }

    const modelInfoMap = {
        "Embedding-V1": {
            endpoint: "/embeddings/embedding-v1",
            required_keys: ["input"],
            optional_keys: ["user_id"],
        },
        "bge-large-en": {
            endpoint: "/embeddings/bge_large_en",
            required_keys: ["input"],
            optional_keys: ["user_id"],
        },
        "bge-large-zh": {
            endpoint: "/embeddings/bge_large_zh",
            required_keys: ["input"],
            optional_keys: ["user_id"],
        },
        "tao-8k": {
            endpoint: "/embeddings/tao_8k",
            required_keys: ["input"],
            optional_keys: ["user_id"],
        },
        UNSPECIFIED_MODEL: {
            endpoint: "",
            required_keys: ["input"],
            optional_keys: [],
        },
    };

    class Eembedding {
        /**
         * 千帆大模型
         * @param API_KEY API Key，IAM、AK/SK 鉴权时必填
         * @param SECRET_KEY Secret Key，IAM、AK/SK 鉴权时必填
         * @param Type 鉴权方式，默认IAM鉴权，如果使用AK/SK鉴权，请设置为'AK'
         */
        constructor(API_KEY, SECRET_KEY, Type = 'IAM') {
            this.Type = 'IAM';
            this.headers = DEFAULT_HEADERS;
            this.access_token = '';
            this.expires_in = 0;
            this.API_KEY = API_KEY;
            this.SECRET_KEY = SECRET_KEY;
            this.Type = Type;
            this.axiosInstance = axios.create();
        }
        async sendRequest(model, body) {
            const endpoint = getModelEndpoint(model, modelInfoMap);
            const requestBody = getRequestBody(body, version$1);
            // IAM鉴权
            if (this.Type === 'IAM') {
                const config = getIAMConfig(this.API_KEY, this.SECRET_KEY);
                const client = new HttpClient(config);
                const path = `${base_path}${endpoint}`;
                const response = await client.sendRequest('POST', path, requestBody, this.headers);
                return response;
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
                };
                try {
                    const resp = await this.axiosInstance.request(options);
                    return resp.data;
                }
                catch (error) {
                    throw new Error(error);
                }
                // }
            }
            throw new Error(`Unsupported authentication type: ${this.Type}`);
        }
        async embedding(body, model = 'Embedding-V1') {
            return this.sendRequest(model, body);
        }
    }

    exports.ChatCompletion = ChatCompletion;
    exports.Completions = Completions;
    exports.Eembedding = Eembedding;

}));
