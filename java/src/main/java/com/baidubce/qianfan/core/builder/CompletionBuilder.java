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

package com.baidubce.qianfan.core.builder;

import com.baidubce.qianfan.Qianfan;
import com.baidubce.qianfan.model.completion.CompletionRequest;
import com.baidubce.qianfan.model.completion.CompletionResponse;

import java.util.Iterator;
import java.util.List;

public class CompletionBuilder extends BaseBuilder<CompletionBuilder> {
    private String prompt;

    private Double temperature;

    private Integer topK;

    private Double topP;

    private Double penaltyScore;

    private List<String> stop;

    public CompletionBuilder() {
        super();
    }

    public CompletionBuilder(Qianfan qianfan) {
        super(qianfan);
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

    public CompletionRequest build() {
        return new CompletionRequest()
                .setPrompt(prompt)
                .setTemperature(temperature)
                .setTopK(topK)
                .setTopP(topP)
                .setPenaltyScore(penaltyScore)
                .setStop(stop)
                .setModel(super.getModel())
                .setEndpoint(super.getEndpoint())
                .setUserId(super.getUserId())
                .setExtraParameters(super.getExtraParameters());
    }

    public CompletionResponse execute() {
        return super.getQianfan().completion(build());
    }

    public Iterator<CompletionResponse> executeStream() {
        return super.getQianfan().completionStream(build());
    }
}
