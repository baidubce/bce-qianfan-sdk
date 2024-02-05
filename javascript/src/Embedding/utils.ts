import {QfLLMInfoMap} from '../interface';

/**
 * 对话请求公共服务模型列表
 */
export type EmbeddingModel =
    | "Embedding-V1"
    | "bge-large-en"
    | "bge-large-zh"
    | "tao-8k"

export const modelInfoMap: QfLLMInfoMap = {
    "Embedding-V1": {
        endpoint: "/embeddings/embedding-v1",
        required_keys: ["input"],
        optional_keys: ["user_id"],
    },
    "bge-large-en": {
        endpoint: "/embeddings/bge_large_en",
        required_keys: ["input"],
        optional_keys: ["user_id"],
    },
    "bge-large-zh": {
        endpoint: "/embeddings/bge_large_zh",
        required_keys: ["input"],
        optional_keys: ["user_id"],
    },
    "tao-8k": {
        endpoint: "/embeddings/tao_8k",
        required_keys: ["input"],
        optional_keys: ["user_id"],
    },
    UNSPECIFIED_MODEL:{
        endpoint: "",
        required_keys: ["input"],
        optional_keys: [],
    },
};