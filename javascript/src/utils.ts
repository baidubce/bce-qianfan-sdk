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

import axios, {AxiosRequestConfig} from 'axios';
import * as dotenv from "dotenv";

import {base_host, base_path, api_base} from './constant';
import {AccessTokenResp, ChatBody, CompletionBody, EmbeddingBody, IAMConfig, QfLLMInfoMap} from './interface';

dotenv.config();

/**
 * 使用 AK，SK 生成鉴权签名（Access Token）
 * @return string 鉴权签名信息（Access Token）
 */

export async function getAccessToken(
    API_KEY: string,
    SECRET_KEY: string,
    headers: AxiosRequestConfig['headers']
): Promise<AccessTokenResp> {
    const url = `https://aip.baidubce.com/oauth/2.0/token?grant_type=client_credentials&client_id=${API_KEY}&client_secret=${SECRET_KEY}`;
    const resp = await axios.post(url, {}, {headers, withCredentials: false});
    if (resp.data?.error && resp.data?.error_description) {
        throw new Error(resp.data.error_description);
    }
    const expires_in = resp.data.expires_in + Date.now() / 1000;
    return {
        access_token: resp.data.access_token,
        expires_in,
    };
}

export function getIAMConfig(ak: string, sk: string): IAMConfig {
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
export function getRequestBody(body: ChatBody | CompletionBody | EmbeddingBody, version: string): string {
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
export const getPath = (model: string, modelInfoMap: QfLLMInfoMap, Authentication:string, endpoint: string = '', type?: string): string => {
    let path: string;
    if (model && modelInfoMap[model]) {
        const _endpoint = getModelEndpoint(model, modelInfoMap);
        path = Authentication ==='IAM' ? `${base_path}${_endpoint}` : `${api_base}${_endpoint}`;
    } else if (endpoint && type) {
        path = Authentication ==='IAM' ? `${base_path}/${type}/${endpoint}` : `${api_base}/${type}/${endpoint}`;
    } else {
        throw new Error('Path not found');
    }
    return path;
};

export const castToError = (err: any): Error => {
    if (err instanceof Error) return err;
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