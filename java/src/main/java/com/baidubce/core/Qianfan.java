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

package com.baidubce.core;

import com.baidubce.core.auth.Auth;
import com.baidubce.core.auth.IAuth;
import com.baidubce.core.builder.ChatBuilder;
import com.baidubce.core.builder.CompletionBuilder;
import com.baidubce.core.builder.EmbeddingBuilder;
import com.baidubce.model.ApiErrorResponse;
import com.baidubce.model.chat.ChatRequest;
import com.baidubce.model.chat.ChatResponse;
import com.baidubce.model.completion.CompletionRequest;
import com.baidubce.model.completion.CompletionResponse;
import com.baidubce.model.constant.ModelEndpoint;
import com.baidubce.model.embedding.EmbeddingRequest;
import com.baidubce.model.embedding.EmbeddingResponse;
import com.baidubce.model.exception.ApiException;
import com.baidubce.model.exception.QianfanException;
import com.baidubce.model.exception.RequestException;
import com.baidubce.util.Json;
import com.baidubce.util.StringUtils;
import com.baidubce.util.http.HttpClient;
import com.baidubce.util.http.HttpRequest;
import com.baidubce.util.http.HttpResponse;

import java.util.Iterator;

public class Qianfan {
    private final IAuth auth;

    public Qianfan() {
        this.auth = Auth.create();
    }

    public Qianfan(String accessKey, String secretKey) {
        this.auth = Auth.create(accessKey, secretKey);
    }

    public Qianfan(String type, String accessKey, String secretKey) {
        this.auth = Auth.create(type, accessKey, secretKey);
    }

    public ChatBuilder chatCompletion() {
        return new ChatBuilder(this);
    }

    public ChatResponse chatCompletion(ChatRequest request) {
        return request(request.getEndpoint(), request, ChatResponse.class);
    }

    public Iterator<ChatResponse> chatCompletionStream(ChatRequest request) {
        request.setStream(true);
        return requestStream(request.getEndpoint(), request, ChatResponse.class);
    }

    public CompletionBuilder completion() {
        return new CompletionBuilder(this);
    }

    public CompletionResponse completion(CompletionRequest request) {
        return request(request.getEndpoint(), request, CompletionResponse.class);
    }

    public Iterator<CompletionResponse> completionStream(CompletionRequest request) {
        request.setStream(true);
        return requestStream(request.getEndpoint(), request, CompletionResponse.class);
    }

    public EmbeddingBuilder embedding() {
        return new EmbeddingBuilder(this);
    }

    public EmbeddingResponse embedding(EmbeddingRequest request) {
        return request(request.getEndpoint(), request, EmbeddingResponse.class);
    }

    private <T> T request(String endpoint, Object body, Class<T> responseClazz) {
        String url = ModelEndpoint.getUrl(endpoint);
        try {
            HttpRequest request = HttpClient.request().post(url).body(body);
            HttpResponse<T> resp = auth.signRequest(request).executeJson(responseClazz);
            if (resp.getCode() != 200) {
                throw new ApiException(String.format("Request failed with status code %d: %s", resp.getCode(), resp.getStringBody()));
            }
            ApiErrorResponse errorResp = Json.deserialize(resp.getStringBody(), ApiErrorResponse.class);
            if (StringUtils.isNotEmpty(errorResp.getErrorMsg())) {
                throw new ApiException("Request failed with api error", errorResp);
            }
            return resp.getBody();
        } catch (QianfanException e) {
            throw e;
        } catch (Exception e) {
            throw new RequestException(String.format("Request failed: %s", e.getMessage()), e);
        }
    }

    private <T> Iterator<T> requestStream(String endpoint, Object body, Class<T> responseClazz) {
        String url = ModelEndpoint.getUrl(endpoint);
        try {
            HttpRequest request = HttpClient.request().post(url).body(body);
            HttpResponse<Iterator<String>> resp = auth.signRequest(request).executeSSE();
            if (resp.getCode() != 200) {
                throw new ApiException(String.format("Request failed with status code %d: %s", resp.getCode(), resp.getStringBody()));
            }
            return new StreamIterator<>(resp.getBody(), responseClazz);
        } catch (QianfanException e) {
            throw e;
        } catch (Exception e) {
            throw new RequestException(String.format("Request failed: %s", e.getMessage()), e);
        }
    }

    private static class StreamIterator<T> implements Iterator<T> {
        private final Iterator<String> sseIterator;
        private final Class<T> responseClazz;

        public StreamIterator(Iterator<String> sseIterator, Class<T> responseClazz) {
            this.sseIterator = sseIterator;
            this.responseClazz = responseClazz;
        }

        @Override
        public boolean hasNext() {
            return sseIterator.hasNext();
        }

        @Override
        public T next() {
            String event = sseIterator.next().replaceFirst("data: ", "");
            // Skip sse empty line
            sseIterator.next();
            return Json.deserialize(event, responseClazz);
        }
    }
}