/*
 * Copyright (c) 2024 Baidu, Inc. All Rights Reserved.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

package com.baidubce.model.constant;

import java.util.HashMap;
import java.util.Map;

public class ModelEndpoint {
    public static final String CHAT = "chat";
    public static final String COMPLETIONS = "completions";
    public static final String EMBEDDINGS = "embeddings";

    private static final String DEFAULT_CHAT_MODEL = "ERNIE-Bot-turbo";

    private static final String DEFAULT_COMPLETION_MODEL = "ERNIE-Bot-turbo";

    private static final String DEFAULT_EMBEDDING_MODEL = "Embedding-V1";

    private static final String QIANFAN_URL_PREFIX = "https://aip.baidubce.com/rpc/2.0/ai_custom/v1/wenxinworkshop";

    private static final Map<String, String> CHAT_MODEL_ENDPOINTS = new HashMap<>();

    private static final Map<String, String> COMPLETION_MODEL_ENDPOINTS = new HashMap<>();

    private static final Map<String, String> EMBEDDING_MODEL_ENDPOINTS = new HashMap<>();

    private static final Map<String, String> UNKNOWN_MODEL_ENDPOINTS = new HashMap<>(0);

    static {
        CHAT_MODEL_ENDPOINTS.put("ERNIE-Bot-turbo", "/chat/eb-instant");
        CHAT_MODEL_ENDPOINTS.put("ERNIE-Bot", "/chat/completions");
        CHAT_MODEL_ENDPOINTS.put("ERNIE-Bot-4", "/chat/completions_pro");
        CHAT_MODEL_ENDPOINTS.put("ERNIE-Bot-8k", "/chat/ernie_bot_8k");
        CHAT_MODEL_ENDPOINTS.put("ERNIE-Speed", "/chat/eb_speed");
        CHAT_MODEL_ENDPOINTS.put("ERNIE-Bot-turbo-AI", "/chat/ai_apaas");
        CHAT_MODEL_ENDPOINTS.put("EB-turbo-AppBuilder", "/chat/ai_apaas");
        CHAT_MODEL_ENDPOINTS.put("BLOOMZ-7B", "/chat/bloomz_7b1");
        CHAT_MODEL_ENDPOINTS.put("Llama-2-7b-chat", "/chat/llama_2_7b");
        CHAT_MODEL_ENDPOINTS.put("Llama-2-13b-chat", "/chat/llama_2_13b");
        CHAT_MODEL_ENDPOINTS.put("Llama-2-70b-chat", "/chat/llama_2_70b");
        CHAT_MODEL_ENDPOINTS.put("Qianfan-BLOOMZ-7B-compressed", "/chat/qianfan_bloomz_7b_compressed");
        CHAT_MODEL_ENDPOINTS.put("Qianfan-Chinese-Llama-2-7B", "/chat/qianfan_chinese_llama_2_7b");
        CHAT_MODEL_ENDPOINTS.put("ChatGLM2-6B-32K", "/chat/chatglm2_6b_32k");
        CHAT_MODEL_ENDPOINTS.put("AquilaChat-7B", "/chat/aquilachat_7b");
        CHAT_MODEL_ENDPOINTS.put("XuanYuan-70B-Chat-4bit", "/chat/xuanyuan_70b_chat");
        CHAT_MODEL_ENDPOINTS.put("Qianfan-Chinese-Llama-2-13B", "/chat/qianfan_chinese_llama_2_13b");
        CHAT_MODEL_ENDPOINTS.put("ChatLaw", "/chat/chatlaw");
        CHAT_MODEL_ENDPOINTS.put("Yi-34B-Chat", "/chat/yi_34b_chat");

        COMPLETION_MODEL_ENDPOINTS.put("SQLCoder-7B", "/completions/sqlcoder_7b");
        COMPLETION_MODEL_ENDPOINTS.put("CodeLlama-7b-Instruct", "/completions/codellama_7b_instruct");

        EMBEDDING_MODEL_ENDPOINTS.put("Embedding-V1", "/embeddings/embedding-v1");
        EMBEDDING_MODEL_ENDPOINTS.put("bge-large-en", "/embeddings/bge_large_en");
        EMBEDDING_MODEL_ENDPOINTS.put("bge-large-zh", "/embeddings/bge_large_zh");
        EMBEDDING_MODEL_ENDPOINTS.put("tao-8k", "/embeddings/tao_8k");
    }

    private ModelEndpoint() {
    }

    public static String getUrl(String endpoint) {
        return QIANFAN_URL_PREFIX + endpoint;
    }

    public static String getEndpoint(String type, String model) {
        return getEndpoint(type, model, null);
    }

    public static String getEndpoint(String type, String model, String endpoint) {
        String finalEndpoint = endpoint;

        Map<String, String> modelMap;
        String defaultModel = null;
        switch (type) {
            case CHAT:
                modelMap = CHAT_MODEL_ENDPOINTS;
                defaultModel = DEFAULT_CHAT_MODEL;
                break;
            case COMPLETIONS:
                modelMap = COMPLETION_MODEL_ENDPOINTS;
                defaultModel = DEFAULT_COMPLETION_MODEL;
                break;
            case EMBEDDINGS:
                modelMap = EMBEDDING_MODEL_ENDPOINTS;
                defaultModel = DEFAULT_EMBEDDING_MODEL;
                break;
            default:
                modelMap = UNKNOWN_MODEL_ENDPOINTS;
        }

        String modelEndpoint = modelMap.get(model);
        if (modelEndpoint != null) {
            finalEndpoint = modelEndpoint;
        }

        if (finalEndpoint == null) {
            finalEndpoint = modelMap.get(defaultModel);
        }

        return finalEndpoint;
    }
}
