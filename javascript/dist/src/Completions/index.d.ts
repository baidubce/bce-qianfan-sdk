import { CompletionModel } from './utils';
import { RespBase, CompletionBody } from '../interface';
export declare class Completions {
    private API_KEY;
    private SECRET_KEY;
    private Type?;
    private Endpoint?;
    private headers;
    private axiosInstance;
    access_token: string;
    expires_in: number;
    /**
     * 千帆大模型
     * @param API_KEY API Key，IAM、AK/SK 鉴权时必填
     * @param SECRET_KEY Secret Key，IAM、AK/SK 鉴权时必填
     * @param Type 鉴权方式，默认IAM鉴权，如果使用AK/SK鉴权，请设置为'AK'
     * @param Endpoint 请求地址，默认使用千帆大模型服务
     */
    constructor(API_KEY: string, SECRET_KEY: string, Type?: string, Endpoint?: string);
    private sendRequest;
    completions(body: CompletionBody, model?: CompletionModel): Promise<RespBase>;
}
export default Completions;
