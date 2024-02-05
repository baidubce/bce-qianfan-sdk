import { ChatBody, ChatResp } from '../interface';
export declare class ChatCompletion {
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
    chat(body: ChatBody, model: 'ERNIE-Bot-turbo'): Promise<ChatResp>;
}
export default ChatCompletion;
