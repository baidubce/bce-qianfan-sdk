import { BaseClient } from '../Base';
import { EmbeddingBody, EmbeddingResp } from '../interface';
import { EmbeddingModel } from './utils';
declare class Eembedding extends BaseClient {
    /**
     * 向量化
     * @param body 请求体
     * @param model 向量化模型，默认为'Embedding-V1'
     * @returns Promise<Resp | AsyncIterable<Resp>>
     */
    embedding(body: EmbeddingBody, model?: EmbeddingModel): Promise<EmbeddingResp>;
}
export default Eembedding;
