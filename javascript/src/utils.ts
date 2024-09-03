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

import HttpClient from './HttpClient';
import Fetch from './Fetch';
import {BASE_PATH, DEFAULT_CONFIG, DEFAULT_HEADERS} from './constant';
import {IAMConfig, QfLLMInfoMap, ReqBody, DefaultConfig} from './interface';
import * as packageJson from '../package.json';

/**
 * 获取当前运行环境
 *
 * @returns 如果运行在浏览器中，返回 'browser'；如果运行在 Node.js 环境中，返回 'node'；否则返回 'unknown'
 */
export function getCurrentEnvironment() {
    if (typeof window !== 'undefined') {
        return 'browser';
    }
    else if (typeof process !== 'undefined' && process?.release?.name === 'node') {
        return 'node';
    }
    return 'unknown';
}

/**
 * 获取访问令牌的URL地址
 *
 * @param QIANFAN_AK 百度云AK
 * @param QIANFAN_SK 百度云SK
 * @returns 返回访问令牌的URL地址
 */
export function getAccessTokenUrl(qianfanAk: string, qianfanSk: string, qianfanBaseUrl: string): string {
    // eslint-disable-next-line max-len
    return `${qianfanBaseUrl}/oauth/2.0/token?grant_type=client_credentials&client_id=${qianfanAk}&client_secret=${qianfanSk}`;
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
export function getRequestBody(body: ReqBody, model, version: string): string {
    const request_source
        = getCurrentEnvironment() === 'browser' ? `qianfan_fe_sdk_v${version}` : `qianfan_js_sdk_v${version}`;

    const modifiedBody = {
        ...body,
        model,
        extra_parameters: {
            ...body.extra_parameters,
            request_source,
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
    // 动态获取模型兜底
    return endpoint ?? '';
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
    model?: string;
    modelInfoMap?: QfLLMInfoMap;
    Authentication: 'IAM' | 'AK'; // 假设 Authentication 只能是 'IAM' 或 'AK'
    api_base: string;
    endpoint?: string;
    type?: string;
}): string => {
    if (endpoint && type) {
        const basePath = Authentication === 'IAM' ? BASE_PATH : api_base;
        const suffix = type === 'plugin' ? '/' : `/${type}/`;
        return `${basePath}${suffix}${endpoint}`;
    }
    else if (model && modelInfoMap && modelInfoMap[model]) {
        const modelEndpoint = getModelEndpoint(model, modelInfoMap);
        return Authentication === 'IAM' ? `${BASE_PATH}${modelEndpoint}` : `${api_base}${modelEndpoint}`;
    }
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
export function getDefaultConfig(): DefaultConfig {
    const envVariables = Object.keys(DEFAULT_CONFIG);
    if (getCurrentEnvironment() === 'browser') {
        return {...DEFAULT_CONFIG};
    }
    require('dotenv').config();
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
    model?: string;
    modelInfoMap?: QfLLMInfoMap;
    baseUrl: string;
    body?: ReqBody;
    endpoint?: string;
    type?: string;
}): {
    AKPath: string;
    requestBody: string;
} {
    const api_base = baseUrl + BASE_PATH;
    const AKPath = getPath({
        model,
        modelInfoMap,
        Authentication: 'AK',
        api_base,
        endpoint,
        type,
    });
    const requestBody = getRequestBody(body, model, packageJson.version);
    return {
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

/**
 * 检查是否满足打开TPM的条件。
 * 条件包括：环境变量 `QIANFAN_TPM_LIMIT` 设定的限制值（如果存在）和header的 `val` 都必须大于0。
 * @param {number} val - 用于检查的值，预期为正数。
 * @returns {boolean} - 如果满足条件则返回true，否则返回false。
 */
export function isOpenTpm(val): boolean {
    const envToken = Number(readEnvVariable('QIANFAN_TPM_LIMIT')) ?? 0;
    return envToken > 0 || val > 0;
}

/**
 * 将对象的键名转换为大写形式
 *
 * @param obj 需要转换键名的对象
 * @returns 返回键名已转换为大写形式的新对象
 */
export function convertKeysToUppercase(obj) {
    return Object.keys(obj).reduce((acc, key) => {
        const uppercaseKey = key.toUpperCase();
        acc[uppercaseKey] = obj[key];
        return acc;
    }, {});
}

/**
 * 将给定的 model 字符串转换为大写，并将给定的 modelMap 中的键转换为大写形式
 *
 * @param model 需要转换为大写的字符串
 * @param modelMap 可选的 QfLLMInfoMap 类型对象，用于转换键为大写形式
 * @returns 返回包含转换后大写 model 字符串和转换后大写键的 modelMap 对象的对象
 */
export function getUpperCaseModelAndModelMap(model: string, modelMap?: QfLLMInfoMap) {
    if (typeof model !== 'string' || model.trim() === '') {
        return {
            modelInfoMapUppercase: modelMap,
            modelUppercase: '',
        };
    }
    const modelInfoMapUppercase = convertKeysToUppercase(modelMap);
    const modelUppercase = model.toUpperCase();
    const modelLowercase = model.toLowerCase();
    return {
        modelInfoMapUppercase,
        modelUppercase,
        modelLowercase,
    };
}

/**
 * 将 Headers 对象解析为键值对形式的对象
 *
 * @param headers Headers 对象
 * @returns 返回键值对形式的对象
 */
export function parseHeaders(headers): {[key: string]: string} {
    const headerObj: {[key: string]: string} = {};
    headers.forEach((value, key) => {
        headerObj[key] = value;
    });
    return headerObj;
}

interface Variables {
    [key: string]: any;
}

/**
 * 设置浏览器变量
 *
 * @param variables 要设置的变量对象，其中每个属性名对应一个变量名，属性值对应变量的值
 * @returns 无返回值
 */
export function setBrowserVariable(variables: Variables): void {
    Object.entries(variables).forEach(([key, value]) => {
        DEFAULT_CONFIG[key] = value;
    });
}

function baseActionUrl(route: string, action: string): string {
    return !action ? route : `${route}?Action=${action}`;
}

interface ConsoleActionParams {
    base_api_route: string;
    data?: Record<string, any>;
    action?: string;
}

/**
 * consoleApi 开放入口
 *
 * @param base_api_route 基础API路由，类型为字符串
 * @param body 查询参数，类型为任意类型
 * @param action 可选参数，方法名称，类型为字符串
 * @returns 返回任意类型
 */
export async function consoleAction({base_api_route, data, action}: ConsoleActionParams): Promise<any> {
    const config = getDefaultConfig();
    // IAM鉴权，先判断是否有IAM的key
    if (!(config.QIANFAN_ACCESS_KEY && config.QIANFAN_SECRET_KEY)) {
        throw new Error('请设置QIANFAN_ACCESS_KEY/QIANFAN_SECRET_KEY');
    }
    // 鉴权
    const httpClientConfig = getIAMConfig(
        config.QIANFAN_ACCESS_KEY,
        config.QIANFAN_SECRET_KEY,
        config.QIANFAN_CONSOLE_API_BASE_URL
    );
    const client = new HttpClient(httpClientConfig);

    const normalizedRoute = base_api_route.startsWith('/') ? base_api_route.slice(1) : base_api_route;
    const apiRoute = `${config.QIANFAN_CONSOLE_API_BASE_URL}/${normalizedRoute}`;

    const baseParams = {
        httpMethod: 'POST',
        path: apiRoute,
        body: data && JSON.stringify(data),
        headers: {
            ...DEFAULT_HEADERS,
        },
    };
    const fetchOptions = await client.getSignature(
        action ? Object.assign({}, baseParams, {params: {Action: action}}) : baseParams
    );
    const fetchInstance = new Fetch();
    try {
        const {url, ...rest} = fetchOptions;
        const resp = await fetchInstance.makeRequest(baseActionUrl(url, action), rest);
        return resp;
    }
    catch (error) {
        throw error;
    }
}
