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

import com.baidubce.core.builder.ChatBuilder;
import com.baidubce.core.builder.CompletionBuilder;
import com.baidubce.core.builder.EmbeddingBuilder;
import com.baidubce.model.chat.ChatRequest;
import com.baidubce.model.chat.ChatResponse;
import com.baidubce.model.completion.CompletionRequest;
import com.baidubce.model.completion.CompletionResponse;
import com.baidubce.model.constant.ModelEndpoint;
import com.baidubce.model.embedding.EmbeddingRequest;
import com.baidubce.model.embedding.EmbeddingResponse;
import com.baidubce.model.exception.QianfanException;
import com.baidubce.util.Json;
import com.baidubce.util.http.HttpClient;
import com.baidubce.util.http.HttpRequest;
import com.baidubce.util.http.HttpResponse;

import java.util.Iterator;

public class Qianfan {
    private final IAMAuth iamAuth;

    public Qianfan(String apiKey, String secretKey) {
        this.iamAuth = new IAMAuth(apiKey, secretKey);
    }

    public ChatBuilder chatCompletion() {
        return new ChatBuilder(this);
    }

    public ChatResponse chatCompletion(String endpoint, ChatRequest request) {
        return request(endpoint, request, ChatResponse.class);
    }

    public Iterator<ChatResponse> chatCompletionStream(String endpoint, ChatRequest request) {
        request.setStream(true);
        return requestStream(endpoint, request, ChatResponse.class);
    }

    public CompletionBuilder completion() {
        return new CompletionBuilder(this);
    }

    public CompletionResponse completion(String endpoint, CompletionRequest request) {
        return request(endpoint, request, CompletionResponse.class);
    }

    public Iterator<CompletionResponse> completionStream(String endpoint, CompletionRequest request) {
        request.setStream(true);
        return requestStream(endpoint, request, CompletionResponse.class);
    }

    public EmbeddingBuilder embedding() {
        return new EmbeddingBuilder(this);
    }

    public EmbeddingResponse embedding(String endpoint, EmbeddingRequest request) {
        return request(endpoint, request, EmbeddingResponse.class);
    }

    private <T> T request(String endpoint, Object body, Class<T> responseClazz) {
        String url = ModelEndpoint.getUrl(endpoint);
        try {
            HttpRequest request = HttpClient.request()
                    .post(url)
                    .body(body);
            HttpResponse<T> resp = signRequest(request).executeJson(responseClazz);
            if (resp.getCode() != 200) {
                throw new QianfanException("Failed to request " + endpoint + ", response code: " + resp.getCode());
            }
            return resp.getBody();
        } catch (Exception e) {
            throw new QianfanException("Failed to request " + endpoint, e);
        }
    }

    private <T> Iterator<T> requestStream(String endpoint, Object body, Class<T> responseClazz) {
        String url = ModelEndpoint.getUrl(endpoint);
        try {
            HttpRequest request = HttpClient.request()
                    .post(url)
                    .body(body);
            HttpResponse<Iterator<String>> resp = signRequest(request).executeSSE();
            if (resp.getCode() != 200) {
                throw new QianfanException("Failed to request " + endpoint + ", response code: " + resp.getCode());
            }
            return new StreamIterator<>(resp.getBody(), responseClazz);
        } catch (Exception e) {
            throw new QianfanException("Failed to request " + endpoint, e);
        }
    }

    private HttpRequest signRequest(HttpRequest request) {
        try {
            return request
                    .addHeader("Authorization", iamAuth.sign(request.getMethod(), request.getUrl()))
                    .addHeader("X-Bce-Date", iamAuth.getTimestamp());
        } catch (Exception e) {
            throw new QianfanException("Failed to sign request", e);
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