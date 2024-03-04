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

import com.baidubce.util.Pair;
import com.baidubce.util.StringUtils;

import java.util.HashMap;
import java.util.Map;

public class ModelEndpoint {
    public static final String CHAT = "chat";
    public static final String COMPLETIONS = "completions";
    public static final String EMBEDDINGS = "embeddings";

    private static final String ENDPOINT_TEMPLATE = "/%s/%s";

    private static final String DEFAULT_CHAT_MODEL = "ERNIE-Bot-turbo";

    private static final String DEFAULT_COMPLETION_MODEL = "CodeLlama-7b-Instruct";

    private static final String DEFAULT_EMBEDDING_MODEL = "Embedding-V1";

    private static final String QIANFAN_URL_PREFIX = "https://aip.baidubce.com/rpc/2.0/ai_custom/v1/wenxinworkshop";

    private static final Map<String, String> CHAT_MODEL_ENDPOINTS = new HashMap<>();

    private static final Map<String, String> COMPLETION_MODEL_ENDPOINTS = new HashMap<>();

    private static final Map<String, String> EMBEDDING_MODEL_ENDPOINTS = new HashMap<>();

    static {
        CHAT_MODEL_ENDPOINTS.put("ERNIE-Bot-turbo", "eb-instant");
        CHAT_MODEL_ENDPOINTS.put("ERNIE-Bot", "completions");
        CHAT_MODEL_ENDPOINTS.put("ERNIE-Bot-4", "completions_pro");
        CHAT_MODEL_ENDPOINTS.put("ERNIE-Bot-8k", "ernie_bot_8k");
        CHAT_MODEL_ENDPOINTS.put("ERNIE-Speed", "ernie_speed");
        CHAT_MODEL_ENDPOINTS.put("ERNIE-Bot-turbo-AI", "ai_apaas");
        CHAT_MODEL_ENDPOINTS.put("EB-turbo-AppBuilder", "ai_apaas");
        CHAT_MODEL_ENDPOINTS.put("BLOOMZ-7B", "bloomz_7b1");
        CHAT_MODEL_ENDPOINTS.put("Llama-2-7b-chat", "llama_2_7b");
        CHAT_MODEL_ENDPOINTS.put("Llama-2-13b-chat", "llama_2_13b");
        CHAT_MODEL_ENDPOINTS.put("Llama-2-70b-chat", "llama_2_70b");
        CHAT_MODEL_ENDPOINTS.put("Qianfan-BLOOMZ-7B-compressed", "qianfan_bloomz_7b_compressed");
        CHAT_MODEL_ENDPOINTS.put("Qianfan-Chinese-Llama-2-7B", "qianfan_chinese_llama_2_7b");
        CHAT_MODEL_ENDPOINTS.put("ChatGLM2-6B-32K", "chatglm2_6b_32k");
        CHAT_MODEL_ENDPOINTS.put("AquilaChat-7B", "aquilachat_7b");
        CHAT_MODEL_ENDPOINTS.put("XuanYuan-70B-Chat-4bit", "xuanyuan_70b_chat");
        CHAT_MODEL_ENDPOINTS.put("Qianfan-Chinese-Llama-2-13B", "qianfan_chinese_llama_2_13b");
        CHAT_MODEL_ENDPOINTS.put("ChatLaw", "chatlaw");
        CHAT_MODEL_ENDPOINTS.put("Yi-34B-Chat", "yi_34b_chat");

        COMPLETION_MODEL_ENDPOINTS.put("SQLCoder-7B", "sqlcoder_7b");
        COMPLETION_MODEL_ENDPOINTS.put("CodeLlama-7b-Instruct", "codellama_7b_instruct");

        EMBEDDING_MODEL_ENDPOINTS.put("Embedding-V1", "embedding-v1");
        EMBEDDING_MODEL_ENDPOINTS.put("bge-large-en", "bge_large_en");
        EMBEDDING_MODEL_ENDPOINTS.put("bge-large-zh", "bge_large_zh");
        EMBEDDING_MODEL_ENDPOINTS.put("tao-8k", "tao_8k");
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
        Pair<Map<String, String>, String> epModel = getEndpointMapAndDefaultModel(type);
        Map<String, String> modelEndpointMap = epModel.first;
        String defaultModel = epModel.second;

        if (StringUtils.isNotEmpty(endpoint)) {
            return String.format(ENDPOINT_TEMPLATE, type, endpoint);
        }

        if (StringUtils.isNotEmpty(model)) {
            String modelEndpoint = modelEndpointMap.get(model);
            if (modelEndpoint == null) {
                throw new IllegalArgumentException("Model " + model + " is not supported for " + type);
            }
            return String.format(ENDPOINT_TEMPLATE, type, modelEndpoint);
        }

        return String.format(ENDPOINT_TEMPLATE, type, modelEndpointMap.get(defaultModel));
    }

    private static Pair<Map<String, String>, String> getEndpointMapAndDefaultModel(String type) {
        switch (type) {
            case CHAT:
                return new Pair<>(CHAT_MODEL_ENDPOINTS, DEFAULT_CHAT_MODEL);
            case COMPLETIONS:
                return new Pair<>(COMPLETION_MODEL_ENDPOINTS, DEFAULT_COMPLETION_MODEL);
            case EMBEDDINGS:
                return new Pair<>(EMBEDDING_MODEL_ENDPOINTS, DEFAULT_EMBEDDING_MODEL);
            default:
                throw new IllegalArgumentException("Unknown model type: " + type);
        }
    }
}
