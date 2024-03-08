import { BaseClient } from '../Base';
import { CompletionBody, Resp } from '../interface';
import { CompletionModel } from './utils';
declare class Completions extends BaseClient {
    /**
     * 续写
     * @param body 续写请求体
     * @param model 续写模型，默认为 'ERNIE-Bot-turbo'
     * @returns 返回 Promise 对象，异步获取续写结果
     */
    completions(body: CompletionBody, model?: CompletionModel): Promise<Resp | AsyncIterable<Resp>>;
}
export default Completions;
