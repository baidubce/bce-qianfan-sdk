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
import com.baidubce.model.completion.CompletionRequest;
import com.baidubce.model.completion.CompletionResponse;
import com.baidubce.model.constant.ModelEndpoint;
import com.baidubce.model.exception.QianfanException;

import java.util.Iterator;
import java.util.List;

public class CompletionBuilder {
    private Qianfan qianfan;

    private String endpoint;

    private String model;

    private String prompt;

    private Double temperature;

    private Integer topK;

    private Double topP;

    private Double penaltyScore;

    private List<String> stop;

    private String userId;

    public CompletionBuilder() {
    }

    public CompletionBuilder(Qianfan qianfan) {
        this.qianfan = qianfan;
    }

    public CompletionBuilder model(String model) {
        this.model = model;
        return this;
    }

    public CompletionBuilder endpoint(String endpoint) {
        this.endpoint = endpoint;
        return this;
    }

    public CompletionBuilder prompt(String prompt) {
        this.prompt = prompt;
        return this;
    }

    public CompletionBuilder temperature(Double temperature) {
        this.temperature = temperature;
        return this;
    }

    public CompletionBuilder topK(Integer topK) {
        this.topK = topK;
        return this;
    }

    public CompletionBuilder topP(Double topP) {
        this.topP = topP;
        return this;
    }

    public CompletionBuilder penaltyScore(Double penaltyScore) {
        this.penaltyScore = penaltyScore;
        return this;
    }

    public CompletionBuilder stop(List<String> stop) {
        this.stop = stop;
        return this;
    }

    public CompletionBuilder userId(String userId) {
        this.userId = userId;
        return this;
    }

    public CompletionRequest build() {
        String finalEndpoint = ModelEndpoint.getEndpoint(ModelEndpoint.COMPLETIONS, model, endpoint);
        return new CompletionRequest()
                .setEndpoint(finalEndpoint)
                .setPrompt(prompt)
                .setTemperature(temperature)
                .setTopK(topK)
                .setTopP(topP)
                .setPenaltyScore(penaltyScore)
                .setStop(stop)
                .setUserId(userId);
    }

    public CompletionResponse execute() {
        if (qianfan == null) {
            throw new QianfanException("Qianfan client is not set. " +
                    "please create builder from Qianfan client, " +
                    "or use build() to get Request and send it by yourself.");
        }
        return qianfan.completion(build());
    }

    public Iterator<CompletionResponse> executeStream() {
        if (qianfan == null) {
            throw new QianfanException("Qianfan client is not set. " +
                    "please create builder from Qianfan client, " +
                    "or use build() to get Request and send it by yourself.");
        }
        return qianfan.completionStream(build());
    }
}
