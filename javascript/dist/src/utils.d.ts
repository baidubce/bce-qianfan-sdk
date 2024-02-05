import { AxiosRequestConfig, AxiosResponse } from 'axios';
import { AccessTokenResp, ChatBody, CompletionBody, IAMConfig, QfLLMInfoMap } from './interface';
/**
 * 使用 AK，SK 生成鉴权签名（Access Token）
 * @return string 鉴权签名信息（Access Token）
 */
export declare function getAccessToken(API_KEY: string, SECRET_KEY: string, headers: AxiosRequestConfig['headers']): Promise<AccessTokenResp>;
export declare function getIAMConfig(ak: string, sk: string): IAMConfig;
/**
 * 获取请求体
 *
 * @param body 聊天体
 * @param version 版本号
 * @returns 返回JSON格式的字符串
 */
export declare function getRequestBody(body: ChatBody | CompletionBody, version: string): string;
/**
 * 获取模型对应的API端点
 * @param model 模型实例
 * @param modelInfoMap 模型信息映射表
 * @returns 返回模型对应的API端点
 * @throws 当模型信息或API端点不存在时抛出异常
 */
export declare function getModelEndpoint(model: string, modelInfoMap: QfLLMInfoMap): string;
export declare const getPath: (model: string, modelInfoMap: QfLLMInfoMap, Authentication: string, endpoint?: string, type?: string) => string;
export declare function getResponseResult(resp: AxiosResponse): any;
