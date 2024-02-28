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

package com.baidubce.core.builder;

import com.baidubce.core.Qianfan;
import com.baidubce.model.constant.ModelEndpoint;
import com.baidubce.model.embedding.EmbeddingRequest;
import com.baidubce.model.embedding.EmbeddingResponse;
import com.baidubce.model.exception.QianfanException;

import java.util.List;

public class EmbeddingBuilder {
    private Qianfan qianfan;

    private String model;

    private String endpoint;

    private List<String> input;

    private String userId;

    public EmbeddingBuilder() {
    }

    public EmbeddingBuilder(Qianfan qianfan) {
        this.qianfan = qianfan;
    }

    public EmbeddingBuilder model(String model) {
        this.model = model;
        return this;
    }

    public EmbeddingBuilder endpoint(String endpoint) {
        this.endpoint = endpoint;
        return this;
    }

    public EmbeddingBuilder input(List<String> input) {
        this.input = input;
        return this;
    }

    public EmbeddingBuilder userId(String userId) {
        this.userId = userId;
        return this;
    }

    public EmbeddingRequest build() {
        String finalEndpoint = ModelEndpoint.getEndpoint(ModelEndpoint.EMBEDDINGS, model, endpoint);
        return new EmbeddingRequest()
                .setEndpoint(finalEndpoint)
                .setInput(input)
                .setUserId(userId);
    }

    public EmbeddingResponse execute() {
        if (qianfan == null) {
            throw new QianfanException("Qianfan client is not set. " +
                    "please create builder from Qianfan client, " +
                    "or use build() to get Request and send it by yourself.");
        }
        return qianfan.embedding(build());
    }
}
