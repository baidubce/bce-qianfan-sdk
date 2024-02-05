import axios, {AxiosRequestConfig, AxiosResponse} from 'axios';

import {base_host, base_path, api_base} from './constant';
import {AccessTokenResp, ChatBody, CompletionBody, EmbeddingBody, IAMConfig, QfLLMInfoMap} from './interface';
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
        'request_source': `qianfan_appbuilder_${version}`,
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

// 返回结果处理，流式和非流式接口返回结果不同 TODO
export function getResponseResult(resp : AxiosResponse): any {
    const result = resp.data;
}
