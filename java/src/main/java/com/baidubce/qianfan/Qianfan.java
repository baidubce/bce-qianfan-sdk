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

package com.baidubce.qianfan;

import com.baidubce.qianfan.core.builder.ChatBuilder;
import com.baidubce.qianfan.core.builder.CompletionBuilder;
import com.baidubce.qianfan.core.builder.EmbeddingBuilder;
import com.baidubce.qianfan.core.builder.Image2TextBuilder;
import com.baidubce.qianfan.core.builder.Text2ImageBuilder;
import com.baidubce.qianfan.model.BaseRequest;
import com.baidubce.qianfan.model.RateLimitConfig;
import com.baidubce.qianfan.model.RetryConfig;
import com.baidubce.qianfan.model.chat.ChatRequest;
import com.baidubce.qianfan.model.chat.ChatResponse;
import com.baidubce.qianfan.model.completion.CompletionRequest;
import com.baidubce.qianfan.model.completion.CompletionResponse;
import com.baidubce.qianfan.model.embedding.EmbeddingRequest;
import com.baidubce.qianfan.model.embedding.EmbeddingResponse;
import com.baidubce.qianfan.model.image.Image2TextRequest;
import com.baidubce.qianfan.model.image.Image2TextResponse;
import com.baidubce.qianfan.model.image.Text2ImageRequest;
import com.baidubce.qianfan.model.image.Text2ImageResponse;

import java.util.Iterator;

public class Qianfan {
    private final QianfanClient client;

    public Qianfan() {
        this.client = new QianfanClient();
    }

    public Qianfan(String accessKey, String secretKey) {
        this.client = new QianfanClient(accessKey, secretKey);
    }

    public Qianfan(String type, String accessKey, String secretKey) {
        this.client = new QianfanClient(type, accessKey, secretKey);
    }

    public Qianfan setRetryConfig(RetryConfig retryConfig) {
        this.client.setRetryConfig(retryConfig);
        return this;
    }

    public Qianfan setRateLimitConfig(RateLimitConfig rateLimitConfig) {
        this.client.setRateLimitConfig(rateLimitConfig);
        return this;
    }

    public ChatBuilder chatCompletion() {
        return new ChatBuilder(this);
    }

    public ChatResponse chatCompletion(ChatRequest request) {
        return request(request, ChatResponse.class);
    }

    public Iterator<ChatResponse> chatCompletionStream(ChatRequest request) {
        request.setStream(true);
        return requestStream(request, ChatResponse.class);
    }

    public CompletionBuilder completion() {
        return new CompletionBuilder(this);
    }

    public CompletionResponse completion(CompletionRequest request) {
        return request(request, CompletionResponse.class);
    }

    public Iterator<CompletionResponse> completionStream(CompletionRequest request) {
        request.setStream(true);
        return requestStream(request, CompletionResponse.class);
    }

    public EmbeddingBuilder embedding() {
        return new EmbeddingBuilder(this);
    }

    public EmbeddingResponse embedding(EmbeddingRequest request) {
        return request(request, EmbeddingResponse.class);
    }

    public Text2ImageBuilder text2Image() {
        return new Text2ImageBuilder(this);
    }

    public Text2ImageResponse text2Image(Text2ImageRequest request) {
        return request(request, Text2ImageResponse.class);
    }

    public Image2TextBuilder image2Text() {
        return new Image2TextBuilder(this);
    }

    public Image2TextResponse image2Text(Image2TextRequest request) {
        return request(request, Image2TextResponse.class);
    }

    public Iterator<Image2TextResponse> image2TextStream(Image2TextRequest request) {
        request.setStream(true);
        return requestStream(request, Image2TextResponse.class);
    }

    public <T, U extends BaseRequest<U>> T request(BaseRequest<U> request, Class<T> responseClass) {
        return client.request(request, responseClass);
    }

    public <T, U extends BaseRequest<U>> Iterator<T> requestStream(BaseRequest<U> request, Class<T> responseClass) {
        return client.requestStream(request, responseClass);
    }
}