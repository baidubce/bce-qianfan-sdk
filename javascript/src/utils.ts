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

import {BASE_PATH, DEFAULT_CONFIG} from './constant';
import {IAMConfig, QfLLMInfoMap, ReqBody} from './interface';
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

export function getIAMConfig(ak: string, sk: string, baseUrl: string): IAMConfig {
    return {
        credentials: {
            ak,
            sk,
        },
        endpoint: baseUrl,
    };
}

/**
 * 获取请求体
 *
 * @param body 聊天体
 * @param version 版本号
 * @returns 返回JSON格式的字符串
 */
export function getRequestBody(body: ReqBody, version: string): string {
    const modifiedBody = {
        ...body,
        extra_parameters: {
            ...body.extra_parameters,
            request_source: `qianfan_js_sdk_v${version}`,
        },
    };
    return JSON.stringify(modifiedBody);
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
export const getPath = ({
    model,
    modelInfoMap,
    Authentication,
    api_base,
    endpoint = '',
    type,
}: {
    model?: string,
    modelInfoMap?: QfLLMInfoMap,
    Authentication: 'IAM' | 'AK', // 假设 Authentication 只能是 'IAM' 或 'AK'
    api_base: string,
    endpoint?: string,
    type?: string,
}): string => {
    if (model && modelInfoMap && modelInfoMap[model]) {
        const modelEndpoint = getModelEndpoint(model, modelInfoMap);
        return Authentication === 'IAM'
            ? `${BASE_PATH}${modelEndpoint}`
            : `${api_base}${modelEndpoint}`;
    }
    else if (endpoint && type) {
        const boundary = type === 'plugin' ? '/' : ''; // 考虑将 '/' 的逻辑处理更明确化
        return Authentication === 'IAM'
            ? `${BASE_PATH}/${type}/${endpoint}${boundary}`
            : `${api_base}/${type}/${endpoint}${boundary}`;
    }
    throw new Error('Path not found');

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
    const envVariables = Object.keys(DEFAULT_CONFIG);
    const obj: Record<string, string> = {};
    for (const key of envVariables) {
        const value = process.env[key];
        if (value !== undefined) {
            obj[key] = value;
        }
    }
    return Object.assign({}, DEFAULT_CONFIG, obj);
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
export function getPathAndBody({
    model,
    modelInfoMap,
    baseUrl,
    body,
    endpoint = '',
    type,
}: {
    model?: string,
    modelInfoMap?: QfLLMInfoMap,
    baseUrl: string,
    body?: ReqBody,
    endpoint?: string,
    type?: string
}): {
    IAMPath: string;
    AKPath: string;
    requestBody: string;
} {
    const api_base = baseUrl + BASE_PATH;
    const IAMPath = getPath({
        model,
        modelInfoMap,
        Authentication: 'IAM',
        api_base,
        endpoint,
        type,
    });
    const AKPath = getPath({
        model,
        modelInfoMap,
        Authentication: 'AK',
        api_base,
        endpoint,
        type,
    });
    const requestBody = getRequestBody(body, packageJson.version);
    return {
        IAMPath,
        AKPath,
        requestBody,
    };
}

/**
 * 计算重试延迟时间的函数。
 *
 * @param attempt 当前重试尝试的次数。
 * @param backoff_factor 回避因子，用于控制重试延迟的增长速率。
 * @param retry_max_wait_interval 最大重试等待时间间隔，确保重试延迟不会超过此值。
 * @returns 重试延迟时间（毫秒）。
 */
export function calculateRetryDelay(
    attempt: number,
    backoff_factor: number = 0,
    retry_max_wait_interval: number = 120000
): number {
    return Math.min(retry_max_wait_interval, backoff_factor * Math.pow(2, attempt));
}
