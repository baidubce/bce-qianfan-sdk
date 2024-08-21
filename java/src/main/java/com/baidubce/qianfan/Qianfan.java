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

import com.baidubce.qianfan.core.StreamIterator;
import com.baidubce.qianfan.core.builder.*;
import com.baidubce.qianfan.model.BaseRequest;
import com.baidubce.qianfan.model.BaseResponse;
import com.baidubce.qianfan.model.RateLimitConfig;
import com.baidubce.qianfan.model.RetryConfig;
import com.baidubce.qianfan.model.chat.ChatRequest;
import com.baidubce.qianfan.model.chat.ChatResponse;
import com.baidubce.qianfan.model.completion.CompletionRequest;
import com.baidubce.qianfan.model.completion.CompletionResponse;
import com.baidubce.qianfan.model.console.ConsoleRequest;
import com.baidubce.qianfan.model.console.ConsoleResponse;
import com.baidubce.qianfan.model.embedding.EmbeddingRequest;
import com.baidubce.qianfan.model.embedding.EmbeddingResponse;
import com.baidubce.qianfan.model.image.Image2TextRequest;
import com.baidubce.qianfan.model.image.Image2TextResponse;
import com.baidubce.qianfan.model.image.Text2ImageRequest;
import com.baidubce.qianfan.model.image.Text2ImageResponse;
import com.baidubce.qianfan.model.plugin.PluginRequest;
import com.baidubce.qianfan.model.plugin.PluginResponse;
import com.baidubce.qianfan.model.rerank.RerankRequest;
import com.baidubce.qianfan.model.rerank.RerankResponse;

import java.lang.reflect.Type;


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

    public StreamIterator<ChatResponse> chatCompletionStream(ChatRequest request) {
        request.setStream(true);
        return requestStream(request, ChatResponse.class);
    }

    public CompletionBuilder completion() {
        return new CompletionBuilder(this);
    }

    public CompletionResponse completion(CompletionRequest request) {
        return request(request, CompletionResponse.class);
    }

    public StreamIterator<CompletionResponse> completionStream(CompletionRequest request) {
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

    public StreamIterator<Image2TextResponse> image2TextStream(Image2TextRequest request) {
        request.setStream(true);
        return requestStream(request, Image2TextResponse.class);
    }

    public RerankBuilder rerank() {
        return new RerankBuilder(this);
    }

    public RerankResponse rerank(RerankRequest request) {
        return request(request, RerankResponse.class);
    }

    public PluginBuilder plugin() {
        return new PluginBuilder(this);
    }

    public PluginResponse plugin(PluginRequest request) {
        return request(request, PluginResponse.class);
    }

    public StreamIterator<PluginResponse> pluginStream(PluginRequest request) {
        request.setStream(true);
        return requestStream(request, PluginResponse.class);
    }

    public ConsoleBuilder console() {
        return new ConsoleBuilder(this);
    }

    public <T> ConsoleResponse<T> console(ConsoleRequest request, Type type) {
        return consoleRequest(request, type);
    }

    public <T extends BaseResponse<T>, U extends BaseRequest<U>> T request(BaseRequest<U> request, Class<T> responseClass) {
        return client.request(request, responseClass);
    }

    public <T extends BaseResponse<T>, U extends BaseRequest<U>> StreamIterator<T> requestStream(BaseRequest<U> request, Class<T> responseClass) {
        return client.requestStream(request, responseClass);
    }

    public <T> ConsoleResponse<T> consoleRequest(ConsoleRequest request, Type type) {
        return client.consoleRequest(request, type);
    }
}