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

export const kEscapedMap: Record<string, string> = {
    '!': '%21',
    '\'': '%27',
    '(': '%28',
    ')': '%29',
    '*': '%2A',
};

export function normalize(string: string, encodingSlash?: boolean): string {
    let result = encodeURIComponent(string);
    result = result.replace(/[!'\(\)\*]/g, $1 => kEscapedMap[$1]);

    if (encodingSlash === false) {
        result = result.replace(/%2F/gi, '/');
    }

    return result;
}

export function trim(string: string): string {
    return (string || '').replace(/^\s+|\s+$/g, '');
}

export function urlObjectToPlainObject(url: URL, httpMethod: string, headers: any): Record<string, string> {
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
        headers: headers,
    };
}