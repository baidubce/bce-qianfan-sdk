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

import * as dotenv from 'dotenv';

import {BASE_HOST, BASE_PATH, API_BASE} from './constant';
import {ChatBody, CompletionBody, EmbeddingBody, IAMConfig, QfLLMInfoMap, ReqBody} from './interface';
import * as packageJson from '../package.json';

dotenv.config();

/**
 * 获取访问令牌的URL地址
 *
 * @param QIANFAN_AK 百度云AK
 * @param QIANFAN_SK 百度云SK
 * @returns 返回访问令牌的URL地址
 */
export function getAccessTokenUrl(QIANFAN_AK: string, QIANFAN_SK: string): string {
    return `https://aip.baidubce.com/oauth/2.0/token?grant_type=client_credentials&client_id=${QIANFAN_AK}&client_secret=${QIANFAN_SK}`;
}

export function getIAMConfig(ak: string, sk: string): IAMConfig {
    return {
        credentials: {
            ak,
            sk,
        },
        endpoint: BASE_HOST,
    };
}

/**
 * 获取请求体
 *
 * @param body 聊天体
 * @param version 版本号
 * @returns 返回JSON格式的字符串
 */
export function getRequestBody(body: ChatBody | CompletionBody | EmbeddingBody, version: string): string {
    // 埋点信息
    body.extra_parameters = {
        ...body.extra_parameters,
        request_source: `qianfan_js_sdk_v${version}`,
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
export function getModelEndpoint(model: string, modelInfoMap: QfLLMInfoMap): string {
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
export const getPath = (
    model: string,
    modelInfoMap: QfLLMInfoMap,
    Authentication: string,
    endpoint: string = '',
    type?: string
): string => {
    let path: string;
    if (model && modelInfoMap[model]) {
        const _endpoint = getModelEndpoint(model, modelInfoMap);
        path = Authentication === 'IAM' ? `${BASE_PATH}${_endpoint}` : `${API_BASE}${_endpoint}`;
    }
    else if (endpoint && type) {
        path = Authentication === 'IAM' ? `${BASE_PATH}/${type}/${endpoint}` : `${API_BASE}/${type}/${endpoint}`;
    }
    else {
        throw new Error('Path not found');
    }
    return path;
};

export const castToError = (err: any): Error => {
    if (err instanceof Error) {
        return err;
    }
    return new Error(err);
};

// 读取单个环境变量
export function readEnvVariable(key: string) {
    return process.env[key];
}

/**
 * 获取默认配置
 *
 * @returns 返回一个字符串类型的键值对对象，包含环境变量
 */
export function getDefaultConfig(): Record<string, string> {
    const envVariables = ['QIANFAN_AK', 'QIANFAN_SK', 'QIANFAN_ACCESS_KEY', 'QIANFAN_SECRET_KEY'];
    const obj: Record<string, string> = {};
    for (const key of envVariables) {
        const value = process.env[key];
        if (value !== undefined) {
            obj[key] = value;
        }
    }

    return obj;
}

// 设置环境变量
export function setEnvVariable(key: string, value: string) {
    process.env[key] = value;
}

/**
 * 获取路径和请求体
 *
 * @param model 模型
 * @param modelInfoMap 模型信息映射
 * @param body 请求体，可选
 * @param endpoint 请求路径，可选
 * @param type 请求类型，可选
 * @returns 包含路径和请求体的对象
 */
export function getPathAndBody(
    model: string,
    modelInfoMap: QfLLMInfoMap,
    body?: ReqBody,
    endpoint?: string,
    type?: string
): {
    IAMPath: string;
    AKPath: string;
    requestBody: string; // 根据您的实际情况替换成合适的类型
} {
    const IAMPath = getPath(model, modelInfoMap, 'IAM', endpoint, type);
    const AKPath = getPath(model, modelInfoMap, 'AK', endpoint, type);
    const requestBody = getRequestBody(body, packageJson.version);
    return {
        IAMPath,
        AKPath,
        requestBody,
    };
}
