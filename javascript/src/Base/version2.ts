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

import {getBearToken} from '../utils';

export interface FetchOptionsProps {
    /**
     * appid 应用ID ，不传使用静默 appid
     */
    appid?: string;
    /**
     * 环境变量，可选值为 'node' 或 'browser'
     */
    env: string;
    /**
     * 模型
     */
    model: string;
    /**
     * 请求体
     */
    requestBody: any;
    /**
     * 请求头
     */
    headers: Object;
    /**
     * Qianfan 访问密钥
     */
    qianfanAccessKey?: string;
    /**
     * Qianfan 密钥
     */
    qianfanSecretKey?: string;
    /**
     * Qianfan 基础 URL
     */
    qianfanV2BaseUrl?: string;
    /**
     * 访问令牌
     */
    bear_token?: string;
}


/**
 * 获取版本2的 Fetch 请求选项
 * 当前只支持Node
 *
 * @param {FetchOptionsProps} props 包含所需参数的对象
 * @returns Fetch 请求选项
 */
export const getFetchOptionsV2 = async (props: FetchOptionsProps) => {
    let {
        requestBody,
        headers,
        qianfanAccessKey,
        qianfanSecretKey,
        qianfanV2BaseUrl,
        appid,
        model,
        env,
        bear_token,
    } = props;

    // SDK JS V2 版本目前只支持node环境
    if (env !== 'node') {
        throw new Error('SDK(JS)-V2版本目前只支持node环境');
    }
    // 检查鉴权信息
    if (!qianfanAccessKey || !qianfanSecretKey) {
        throw new Error('请设置QIANFAN_ACCESS_KEY/QIANFAN_SECRET_KEY');
    }
    if (!bear_token) {
        let {token} = await getBearToken();
        bear_token = token;
    }
    if (!bear_token) {
        throw new Error('请设置正确的QIANFAN_ACCESS_KEY/QIANFAN_SECRET_KEY');
    }

    const body = JSON.parse(requestBody);

    return {
        url: qianfanV2BaseUrl,
        method: 'POST',
        headers: {
            ...headers,
            Authorization: `Bearer ${bear_token}`,
            appid,

        },
        body: JSON.stringify({
            ...body,
            model,
        }),
    };
};
