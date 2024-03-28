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

package com.baidubce.qianfan.model.completion;

import com.baidubce.qianfan.model.BaseRequest;
import com.baidubce.qianfan.model.constant.ModelType;

import java.util.List;

public class CompletionRequest extends BaseRequest<CompletionRequest> {
    /**
     * 请求信息
     */
    private String prompt;

    /**
     * 较高的数值会使输出更加随机，而较低的数值会使其更加集中和确定，范围 (0, 1.0]，不能为0
     */
    private Double temperature;

    /**
     * Top-K 采样参数，在每轮token生成时，保留k个概率最高的token作为候选
     */
    private Integer topK;

    /**
     * 影响输出文本的多样性，取值越大，生成文本的多样性越强。取值范围 [0, 1.0]
     */
    private Double topP;

    /**
     * 通过对已生成的token增加惩罚，减少重复生成的现象。说明：值越大表示惩罚越大，取值范围：[1.0, 2.0]
     */
    private Double penaltyScore;

    /**
     * 生成停止标识，当模型生成结果以stop中某个元素结尾时，停止文本生成
     */
    private List<String> stop;

    /**
     * 是否为流式请求
     */
    private Boolean stream;

    @Override
    public String getType() {
        return ModelType.COMPLETIONS;
    }

    public String getPrompt() {
        return prompt;
    }

    public CompletionRequest setPrompt(String prompt) {
        this.prompt = prompt;
        return this;
    }

    public Double getTemperature() {
        return temperature;
    }

    public CompletionRequest setTemperature(Double temperature) {
        this.temperature = temperature;
        return this;
    }

    public Integer getTopK() {
        return topK;
    }

    public CompletionRequest setTopK(Integer topK) {
        this.topK = topK;
        return this;
    }

    public Double getTopP() {
        return topP;
    }

    public CompletionRequest setTopP(Double topP) {
        this.topP = topP;
        return this;
    }

    public Double getPenaltyScore() {
        return penaltyScore;
    }

    public CompletionRequest setPenaltyScore(Double penaltyScore) {
        this.penaltyScore = penaltyScore;
        return this;
    }

    public List<String> getStop() {
        return stop;
    }

    public CompletionRequest setStop(List<String> stop) {
        this.stop = stop;
        return this;
    }

    public Boolean getStream() {
        return stream;
    }

    public CompletionRequest setStream(Boolean stream) {
        this.stream = stream;
        return this;
    }
}
