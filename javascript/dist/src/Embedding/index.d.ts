import { EmbeddingModel } from './utils';
import { EmbeddingBody, EmbeddingResp } from '../interface';
export declare class Eembedding {
    private API_KEY;
    private SECRET_KEY;
    private Type;
    private headers;
    private axiosInstance;
    access_token: string;
    expires_in: number;
    /**
     * 千帆大模型
     * @param API_KEY API Key，IAM、AK/SK 鉴权时必填
     * @param SECRET_KEY Secret Key，IAM、AK/SK 鉴权时必填
     * @param Type 鉴权方式，默认IAM鉴权，如果使用AK/SK鉴权，请设置为'AK'
     */
    constructor(API_KEY: string, SECRET_KEY: string, Type?: string);
    private sendRequest;
    embedding(body: EmbeddingBody, model?: EmbeddingModel): Promise<EmbeddingResp>;
}
export default Eembedding;
