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
    bearer_token?: string;
}


/**
 * 获取版本2的 Fetch 请求选项
 * 当前只支持Node
 *
 * @param {FetchOptionsProps} props 包含所需参数的对象
 * @returns Fetch 请求选项
 */
export const getFetchOptionsV2 = async (props: FetchOptionsProps) => {
    const {
        requestBody,
        headers,
        qianfanAccessKey,
        qianfanSecretKey,
        qianfanV2BaseUrl,
        appid,
        model,
        env,
    } = props;
    let {bearer_token} = props;

    // SDK JS V2 版本目前只支持node环境
    if (env !== 'node') {
        throw new Error('SDK(JS)-V2版本目前只支持node环境');
    }

    if (!bearer_token) {
        // 检查鉴权信息
        if (!qianfanAccessKey || !qianfanSecretKey) {
            throw new Error('请设置QIANFAN_ACCESS_KEY/QIANFAN_SECRET_KEY或BEARER_TOKEN');
        }
        let {token} = await getBearToken();
        if (!token) {
            throw new Error('生成 BearerToken 出错，请设置正确的QIANFAN_ACCESS_KEY/QIANFAN_SECRET_KEY');
        }
        else {
            bearer_token = token;
        }
    }
    const body = JSON.parse(requestBody);

    return {
        url: qianfanV2BaseUrl,
        method: 'POST',
        headers: {
            ...headers,
            Authorization: `Bearer ${bearer_token}`,
            appid,

        },
        body: JSON.stringify({
            ...body,
            model,
        }),
    };
};
