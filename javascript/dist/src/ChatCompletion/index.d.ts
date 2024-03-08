import { BaseClient } from '../Base';
import { ChatBody, Resp } from '../interface';
import { ChatModel } from './utils';
declare class ChatCompletion extends BaseClient {
    /**
     * chat
     * @param body 聊天请求体
     * @param model 聊天模型，默认为 'ERNIE-Bot-turbo'
     * @param stream 是否开启流模式，默认为 false
     * @returns Promise<ChatResp | AsyncIterable<ChatResp>>
     */
    chat(body: ChatBody, model?: ChatModel): Promise<Resp | AsyncIterable<Resp>>;
}
export default ChatCompletion;
