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

package com.baidubce.qianfan.core;

import com.baidubce.qianfan.core.auth.IAMAuth;
import com.baidubce.qianfan.core.auth.IAuth;
import com.baidubce.qianfan.model.console.ConsoleResponse;
import com.baidubce.qianfan.model.console.ListServiceRequest;
import com.baidubce.qianfan.model.console.ListServiceResponse;
import com.baidubce.qianfan.model.console.ServiceItem;
import com.baidubce.qianfan.model.constant.ModelType;
import com.baidubce.qianfan.model.exception.ValidationException;
import com.baidubce.qianfan.util.StringUtils;
import com.baidubce.qianfan.util.TypeRef;
import com.baidubce.qianfan.util.http.HttpClient;
import com.baidubce.qianfan.util.http.HttpResponse;

import java.util.HashMap;
import java.util.List;
import java.util.Map;

public class ModelEndpointRetriever {
    private static final String DEFAULT_CHAT_MODEL = "ERNIE-Bot-turbo";
    private static final String DEFAULT_COMPLETION_MODEL = "CodeLlama-7b-Instruct";
    private static final String DEFAULT_EMBEDDING_MODEL = "Embedding-V1";
    private static final String DEFAULT_TEXT_2_IMAGE_MODEL = "Stable-Diffusion-XL";

    private static final String LIST_MODEL_SERVICE_URL = "%s/wenxinworkshop/service/list";
    private static final String ENDPOINT_TEMPLATE = "/%s/%s";
    private static final int DYNAMIC_MAP_REFRESH_INTERVAL = 3600;
    private static final String[] MODEL_TYPES = {ModelType.CHAT, ModelType.COMPLETIONS, ModelType.EMBEDDINGS, ModelType.TEXT_2_IMAGE, ModelType.IMAGE_2_TEXT};

    // type -> (model -> endpoint)
    private final Map<String, Map<String, String>> typeModelEndpointMap = new HashMap<>();
    private final Map<String, String> defaultTypeModelMap = new HashMap<>();
    private volatile Map<String, Map<String, String>> dynamicTypeModelEndpointMap = new HashMap<>();
    private IAMAuth auth;
    private volatile long dynamicMapExpireAt;

    public ModelEndpointRetriever(IAuth auth) {
        if (auth instanceof IAMAuth) {
            this.auth = (IAMAuth) auth;
        }

        defaultTypeModelMap.put(ModelType.CHAT, DEFAULT_CHAT_MODEL);
        defaultTypeModelMap.put(ModelType.COMPLETIONS, DEFAULT_COMPLETION_MODEL);
        defaultTypeModelMap.put(ModelType.EMBEDDINGS, DEFAULT_EMBEDDING_MODEL);
        defaultTypeModelMap.put(ModelType.TEXT_2_IMAGE, DEFAULT_TEXT_2_IMAGE_MODEL);

        for (String type : MODEL_TYPES) {
            typeModelEndpointMap.put(type, new HashMap<>());
            dynamicTypeModelEndpointMap.put(type, new HashMap<>());
        }

        typeModelEndpointMap.get(ModelType.CHAT).put("ERNIE-4.0-8K", "completions_pro");
        typeModelEndpointMap.get(ModelType.CHAT).put("ERNIE-3.5-8K", "completions");
        typeModelEndpointMap.get(ModelType.CHAT).put("ERNIE-3.5-8K-0205", "ernie-3.5-8k-0205");
        typeModelEndpointMap.get(ModelType.CHAT).put("ERNIE-3.5-8K-1222", "ernie-3.5-8k-1222");
        typeModelEndpointMap.get(ModelType.CHAT).put("ERNIE-Bot-8K", "ernie_bot_8k");
        typeModelEndpointMap.get(ModelType.CHAT).put("ERNIE-3.5-4K-0205", "ernie-3.5-4k-0205");
        typeModelEndpointMap.get(ModelType.CHAT).put("ERNIE-Speed-8K", "ernie_speed");
        typeModelEndpointMap.get(ModelType.CHAT).put("ERNIE-Speed-128K", "ernie-speed-128k");
        typeModelEndpointMap.get(ModelType.CHAT).put("ERNIE-Lite-8K-0922", "eb-instant");
        typeModelEndpointMap.get(ModelType.CHAT).put("ERNIE-Lite-8K-0308", "ernie-lite-8k");
        typeModelEndpointMap.get(ModelType.CHAT).put("ERNIE Speed-AppBuilder", "ai_apaas");
        typeModelEndpointMap.get(ModelType.CHAT).put("Gemma-7B-it", "gemma_7b_it");
        typeModelEndpointMap.get(ModelType.CHAT).put("Yi-34B-Chat", "yi_34b_chat");
        typeModelEndpointMap.get(ModelType.CHAT).put("BLOOMZ-7B", "bloomz_7b1");
        typeModelEndpointMap.get(ModelType.CHAT).put("Qianfan-BLOOMZ-7B-compressed", "qianfan_bloomz_7b_compressed");
        typeModelEndpointMap.get(ModelType.CHAT).put("Mixtral-8x7B-Instruct", "mixtral_8x7b_instruct");
        typeModelEndpointMap.get(ModelType.CHAT).put("Llama-2-7b-chat", "llama_2_7b");
        typeModelEndpointMap.get(ModelType.CHAT).put("Llama-2-13b-chat", "llama_2_13b");
        typeModelEndpointMap.get(ModelType.CHAT).put("Llama-2-70b-chat", "llama_2_70b");
        typeModelEndpointMap.get(ModelType.CHAT).put("Qianfan-Chinese-Llama-2-7B", "qianfan_chinese_llama_2_7b");
        typeModelEndpointMap.get(ModelType.CHAT).put("Qianfan-Chinese-Llama-2-13B", "qianfan_chinese_llama_2_13b");
        typeModelEndpointMap.get(ModelType.CHAT).put("ChatGLM2-6B-32K", "chatglm2_6b_32k");
        typeModelEndpointMap.get(ModelType.CHAT).put("XuanYuan-70B-Chat-4bit", "xuanyuan_70b_chat");
        typeModelEndpointMap.get(ModelType.CHAT).put("ChatLaw", "chatlaw");
        typeModelEndpointMap.get(ModelType.CHAT).put("AquilaChat-7B", "aquilachat_7b");
        typeModelEndpointMap.get(ModelType.COMPLETIONS).put("SQLCoder-7B", "sqlcoder_7b");
        typeModelEndpointMap.get(ModelType.COMPLETIONS).put("CodeLlama-7b-Instruct", "codellama_7b_instruct");
        typeModelEndpointMap.get(ModelType.EMBEDDINGS).put("Embedding-V1", "embedding-v1");
        typeModelEndpointMap.get(ModelType.EMBEDDINGS).put("bge-large-zh", "bge_large_zh");
        typeModelEndpointMap.get(ModelType.EMBEDDINGS).put("bge-large-en", "bge_large_en");
        typeModelEndpointMap.get(ModelType.EMBEDDINGS).put("tao-8k", "tao_8k");
        typeModelEndpointMap.get(ModelType.TEXT_2_IMAGE).put("Stable-Diffusion-XL", "sd_xl");
        // Compatibility for old model names
        typeModelEndpointMap.get(ModelType.CHAT).put("ERNIE-Bot-turbo", "eb-instant");
        typeModelEndpointMap.get(ModelType.CHAT).put("ERNIE-Bot", "completions");
        typeModelEndpointMap.get(ModelType.CHAT).put("ERNIE-Bot-4", "completions_pro");
        typeModelEndpointMap.get(ModelType.CHAT).put("ERNIE-Bot-8k", "ernie_bot_8k");
        typeModelEndpointMap.get(ModelType.CHAT).put("ERNIE-Speed", "ernie_speed");
        typeModelEndpointMap.get(ModelType.CHAT).put("ERNIE-Speed-128k", "ernie_speed");
        typeModelEndpointMap.get(ModelType.CHAT).put("ERNIE-Bot-turbo-AI", "ai_apaas");
        typeModelEndpointMap.get(ModelType.CHAT).put("EB-turbo-AppBuilder", "ai_apaas");
    }

    private static String parseEndpoint(String url) {
        String[] parts = url.split("/");
        return parts[parts.length - 1];
    }

    @SafeVarargs
    private static <K, V> V getFromMultiMap(K key, Map<K, V>... maps) {
        for (Map<K, V> map : maps) {
            if (map.containsKey(key)) {
                return map.get(key);
            }
        }
        return null;
    }

    public String getEndpoint(String type, String model, String endpoint) {
        if (isDynamicMapExpired()) {
            synchronized (this) {
                if (isDynamicMapExpired()) {
                    updateDynamicModelEndpointMap();
                    dynamicMapExpireAt = System.currentTimeMillis() / 1000 + DYNAMIC_MAP_REFRESH_INTERVAL;
                }
            }
        }

        Map<String, String> endpointMap = typeModelEndpointMap.get(type);
        Map<String, String> dynamicEndpointMap = dynamicTypeModelEndpointMap.get(type);
        if (endpointMap == null) {
            throw new ValidationException("Type " + type + " is not supported");
        }

        if (StringUtils.isNotEmpty(endpoint)) {
            return String.format(ENDPOINT_TEMPLATE, type, endpoint);
        }

        if (StringUtils.isNotEmpty(model)) {
            String modelEndpoint = getFromMultiMap(model, dynamicEndpointMap, endpointMap);
            if (modelEndpoint == null) {
                throw new IllegalArgumentException("Model " + model + " is not supported for " + type);
            }
            return String.format(ENDPOINT_TEMPLATE, type, modelEndpoint);
        }

        String defaultModel = defaultTypeModelMap.get(type);
        if (defaultModel == null) {
            throw new ValidationException("No default model for type " + type);
        }
        return String.format(ENDPOINT_TEMPLATE, type, getFromMultiMap(defaultModel, dynamicEndpointMap, endpointMap));
    }

    private boolean isDynamicMapExpired() {
        return System.currentTimeMillis() / 1000 > dynamicMapExpireAt;
    }

    private void updateDynamicModelEndpointMap() {
        String url = String.format(LIST_MODEL_SERVICE_URL, QianfanConfig.getConsoleApiBaseUrl());
        try {
            HttpResponse<ConsoleResponse<ListServiceResponse>> resp = auth.signRequest(HttpClient.request().post(url))
                    .body(new ListServiceRequest())
                    .executeJson(new TypeRef<ConsoleResponse<ListServiceResponse>>() {});

            if (resp.getCode() != 200) {
                return;
            }
            List<ServiceItem> services = resp.getBody().getResult().getCommon();
            if (services.isEmpty()) {
                return;
            }

            Map<String, Map<String, String>> newDynamicMap = new HashMap<>();
            for (String type : MODEL_TYPES) {
                newDynamicMap.put(type, new HashMap<>());
            }
            for (ServiceItem service : services) {
                String apiType = service.getApiType();
                String model = service.getName();
                String endpoint = parseEndpoint(service.getUrl());
                Map<String, String> modelEndpointMap = newDynamicMap.get(apiType);
                if (modelEndpointMap != null) {
                    modelEndpointMap.put(model, endpoint);
                }
            }
            dynamicTypeModelEndpointMap = newDynamicMap;
        } catch (Exception e) {
            // ignored
        }
    }
}
