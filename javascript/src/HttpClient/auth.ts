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

import * as util from 'util';
import * as crypto from 'crypto';
import _ from 'underscore';
import createDebug from 'debug';

import * as H from './headers';
import {normalize, trim} from './strings';

const debug = createDebug('bce-sdk:Auth');

class Auth {
    private ak: string;
    private sk: string;

    constructor(ak: string, sk: string) {
        this.ak = ak;
        this.sk = sk;
    }

    generateAuthorization(
        method: string,
        resource: string,
        params?: Record<string, any>,
        headers?: Record<string, any>,
        timestamp?: number,
        expirationInSeconds?: number,
        headersToSign?: string[]
    ): string {
        const now = this.getTimestamp(timestamp);
        const rawSessionKey = util.format('bce-auth-v1/%s/%s/%d', this.ak, now, expirationInSeconds || 1800);
        debug('rawSessionKey = %j', rawSessionKey);
        const sessionKey = this.hash(rawSessionKey, this.sk);
        const canonicalUri = this.generateCanonicalUri(resource);
        const canonicalQueryString = this.queryStringCanonicalization(params || {});

        const rv = this.headersCanonicalization(headers || {}, headersToSign);
        const canonicalHeaders = rv[0];
        const signedHeaders = rv[1];
        debug('canonicalUri = %j', canonicalUri);
        debug('canonicalQueryString = %j', canonicalQueryString);
        debug('canonicalHeaders = %j', canonicalHeaders);
        debug('signedHeaders = %j', signedHeaders);

        const rawSignature = util.format('%s\n%s\n%s\n%s', method, canonicalUri, canonicalQueryString, canonicalHeaders);
        debug('rawSignature = %j', rawSignature);
        debug('sessionKey = %j', sessionKey);
        const signature = this.hash(rawSignature, sessionKey);

        if (signedHeaders.length) {
            return util.format('%s/%s/%s', rawSessionKey, signedHeaders.join(';'), signature);
        }
        return util.format('%s//%s', rawSessionKey, signature);
    }

    private  normalize(string: string, encodingSlash: boolean = true): string {
        const kEscapedMap: Record<string, string> = {
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

    private getTimestamp(timestamp?: number): string {
        const now = timestamp ? new Date(timestamp * 1000) : new Date();
        return now.toISOString().replace(/\.\d+Z$/, 'Z');
    }

    private generateCanonicalUri(url: string): string {
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

    private queryStringCanonicalization(params: Record<string, any>): string {
        const canonicalQueryString: string[] = [];
        
        Object.keys(params).forEach((key) => {
            if (key.toLowerCase() === H.AUTHORIZATION.toLowerCase()) {
                return;
            }

            const value = params[key] == null ? '' : params[key];
            canonicalQueryString.push(`${key}=${this.normalize(value)}`);
        });

        canonicalQueryString.sort();

        return canonicalQueryString.join('&');
    }

    private headersCanonicalization(headers: Record<string, any>, headersToSign?: string[]): [string, string[]] {
        if (!headersToSign || !headersToSign.length) {
            headersToSign = [H.HOST, H.CONTENT_MD5, H.CONTENT_LENGTH, H.CONTENT_TYPE];
        }
        debug('headers = %j, headersToSign = %j', headers, headersToSign);

        const headersMap: Record<string, boolean> = {};
        headersToSign.forEach((item) => {
            headersMap[item.toLowerCase()] = true;
        });

        const canonicalHeaders: string[] = [];
        Object.keys(headers).forEach((key) => {
            let value = headers[key];
            value = _.isString(value) ? trim(value) : value;
            if (value == null || value === '') {
                return;
            }
            key = key.toLowerCase();
            if (/^x\-bce\-/.test(key) || headersMap[key] === true) {
                canonicalHeaders.push(
                    util.format(
                        '%s:%s',
                        normalize(key),
                        normalize(value)
                    )
                );
            }
        });

        canonicalHeaders.sort();

        const signedHeaders: string[] = [];
        canonicalHeaders.forEach((item) => {
            signedHeaders.push(item.split(':')[0]);
        });

        return [canonicalHeaders.join('\n'), signedHeaders];
    }

    private hash(data: string, key: string): string {
        const sha256Hmac = crypto.createHmac('sha256', key);
        sha256Hmac.update(data);
        return sha256Hmac.digest('hex');
    }
}

export default Auth;
