import { ChatBody, CompletionBody, EmbeddingBody, IAMConfig, QfLLMInfoMap, ReqBody } from './interface';
/**
 * 获取访问令牌的URL地址
 *
 * @param QIANFAN_AK 百度云AK
 * @param QIANFAN_SK 百度云SK
 * @returns 返回访问令牌的URL地址
 */
export declare function getAccessTokenUrl(QIANFAN_AK: string, QIANFAN_SK: string): string;
export declare function getIAMConfig(ak: string, sk: string): IAMConfig;
/**
 * 获取请求体
 *
 * @param body 聊天体
 * @param version 版本号
 * @returns 返回JSON格式的字符串
 */
export declare function getRequestBody(body: ChatBody | CompletionBody | EmbeddingBody, version: string): string;
/**
 * 获取模型对应的API端点
 * @param model 模型实例
 * @param modelInfoMap 模型信息映射表
 * @returns 返回模型对应的API端点
 * @throws 当模型信息或API端点不存在时抛出异常
 */
export declare function getModelEndpoint(model: string, modelInfoMap: QfLLMInfoMap): string;
export declare const getPath: (model: string, modelInfoMap: QfLLMInfoMap, Authentication: string, endpoint?: string, type?: string) => string;
export declare const castToError: (err: any) => Error;
export declare function readEnvVariable(key: string): string;
/**
 * 获取默认配置
 *
 * @returns 返回一个字符串类型的键值对对象，包含环境变量
 */
export declare function getDefaultConfig(): Record<string, string>;
export declare function setEnvVariable(key: string, value: string): void;
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
export declare function getPathAndBody(model: string, modelInfoMap: QfLLMInfoMap, body?: ReqBody, endpoint?: string, type?: string): {
    IAMPath: string;
    AKPath: string;
    requestBody: string;
};
