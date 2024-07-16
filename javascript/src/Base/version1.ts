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
import {getIAMConfig, getPath} from '../utils';
import DynamicModelEndpoint from '../DynamicModelEndpoint';

export interface FetchOptionsProps {
    /**
     * 环境变量，可选值为 'node' 或 'browser'
     */
    env: string;
    /**
     * 类型
     */
    type: string;
    /**
     * 模型
     */
    model: string;
    /**
     * AK路径
     */
    AKPath: string;
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
    qianfanAccessKey: string;
    /**
     * Qianfan 密钥
     */
    qianfanSecretKey: string;
    /**
     * Qianfan AK
     */
    qianfanAk: string;
    /**
     * Qianfan SK
     */
    qianfanSk: string;
    /**
     * Qianfan 基础 URL
     */
    qianfanBaseUrl: string;
    /**
     * Qianfan 控制台 API 基础 URL
     */
    qianfanConsoleApiBaseUrl: string;
    /**
     * 终端点
     */
    Endpoint: string;
    /**
     * 访问令牌
     */
    accessToken: string;
}

/**
 * 获取版本1的 Fetch 请求选项
 *
 * @param {FetchOptionsProps} props 包含所需参数的对象
 * @returns Fetch 请求选项
 * @throws 当环境变量为 'node' 且未设置 AK/SK 或 Qianfan_ACCESS_KEY/Qianfan_SECRET_KEY 时，抛出错误
 * @throws 当环境变量为 'node' 且未找到对应模型时，抛出错误
 * @throws 当环境变量为 'browser' 且 baseUrl 包含了 'aip.baidubce.com' 时，抛出错误
 * @throws 当环境变量为 'browser' 且未找到对应模型时，抛出错误
 */
export const getVersion1FetchOptions = async (props: FetchOptionsProps) => {
    const {
        env,
        type,
        model,
        AKPath,
        requestBody,
        headers,
        qianfanAccessKey,
        qianfanSecretKey,
        qianfanAk,
        qianfanSk,
        qianfanBaseUrl,
        qianfanConsoleApiBaseUrl,
        Endpoint,
        accessToken,
    } = props;

    if (env === 'node') {
        // 检查鉴权信息
        if (!(qianfanAccessKey && qianfanSecretKey) && !(qianfanAk && qianfanSk)) {
            throw new Error('请设置AK/SK或QIANFAN_ACCESS_KEY/QIANFAN_SECRET_KEY');
        }
        // IAM 鉴权
        if (qianfanAccessKey && qianfanSecretKey) {
            const config = getIAMConfig(qianfanAccessKey, qianfanSecretKey, qianfanBaseUrl);
            const client = new HttpClient(config);
            const dynamicModelEndpoint = new DynamicModelEndpoint(client, qianfanConsoleApiBaseUrl, qianfanBaseUrl);
            let IAMPath = '';
            if (Endpoint) {
                IAMPath = getPath({
                    Authentication: 'IAM',
                    api_base: qianfanBaseUrl,
                    endpoint: Endpoint,
                    type,
                });
            }
            else {
                IAMPath = await dynamicModelEndpoint.getEndpoint(type, model);
            }
            if (!IAMPath) {
                throw new Error(`${model} is not supported`);
            }
            const options = await client.getSignature({
                httpMethod: 'POST',
                path: IAMPath,
                body: requestBody,
                headers,
            });
            return options;
        }
        // AK/SK 鉴权
        if (qianfanAk && qianfanSk) {
            const url = `${AKPath}?access_token=${accessToken}`;
            const options = {
                url,
                method: 'POST',
                headers,
                body: requestBody,
            };
            return options;
        }
    }
    else if (env === 'browser') {
        // 浏览器环境 需要设置 proxy
        if (qianfanBaseUrl.includes('aip.baidubce.com')) {
            throw new Error('请设置proxy的baseUrl');
        }
        // 如果设置了管控 api, 则使用管控 api 获取最新模型
        if (qianfanConsoleApiBaseUrl && !qianfanConsoleApiBaseUrl.includes('qianfan.baidubce.com')) {
            const dynamicModelEndpoint = new DynamicModelEndpoint(null, qianfanConsoleApiBaseUrl, qianfanBaseUrl);
            let IAMPath = '';
            if (Endpoint) {
                IAMPath = getPath({
                    Authentication: 'IAM',
                    api_base: qianfanBaseUrl,
                    endpoint: Endpoint,
                    type,
                });
            }
            else {
                IAMPath = await dynamicModelEndpoint.getEndpoint(type, model);
            }
            if (!IAMPath) {
                throw new Error(`${model} is not supported`);
            }
            const options = {
                url: `${qianfanBaseUrl}${IAMPath}`,
                method: 'POST',
                headers,
                body: requestBody,
            };
            return options;
        }

        const url = `${AKPath}`;
        const options = {
            url,
            method: 'POST',
            headers,
            body: requestBody,
        };
        return options;
    }
};
