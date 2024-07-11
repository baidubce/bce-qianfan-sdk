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
import {getIAMConfig} from '../utils';
import {FetchOptionsProps} from './version1';

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
export const getVersion2FetchOptions = async (props: FetchOptionsProps) => {
    const {
        env,
        requestBody,
        headers,
        qianfanAccessKey,
        qianfanSecretKey,
        qianfanBaseUrl,
        qianfanConsoleApiBaseUrl,
    } = props;

    // node 环境 - 检查 IAM 鉴权信息
    if (env === 'node' && !(qianfanAccessKey && qianfanSecretKey)) {
        throw new Error('使用 V2 版本的 API 请设置 QIANFAN_ACCESS_KEY/QIANFAN_SECRET_KEY');
    }
    // browser 环境 - 走代理
    if (env === 'browser' && qianfanBaseUrl.includes('aip.baidubce.com')) {
        throw new Error('请设置 proxy 的 baseUrl');
    }
    else {
        const config = getIAMConfig(qianfanAccessKey, qianfanSecretKey, qianfanConsoleApiBaseUrl);
        const client = new HttpClient(config);
        const IAMPath = '/v2/chat';
        const options = await client.getSignature({
            httpMethod: 'POST',
            path: IAMPath,
            body: requestBody,
            headers,
        });
        return options;
    }
};
