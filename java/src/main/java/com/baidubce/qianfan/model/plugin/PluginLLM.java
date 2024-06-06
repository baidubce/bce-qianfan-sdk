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

package com.baidubce.qianfan.model.plugin;

public class PluginLLM {
    /**
     * 说明：
     * （1）较高的数值会使输出更加随机，而较低的数值会使其更加集中和确定
     * （2）范围 (0, 1.0]，不能为0
     */
    private Double temperature;

    /**
     * 说明：
     * （1）影响输出文本的多样性，取值越大，生成文本的多样性越强
     * （2）取值范围 [0, 1.0]
     */
    private Double topP;

    /**
     * 通过对已生成的token增加惩罚，减少重复生成的现象。说明：
     * （1）值越大表示惩罚越大
     * （2）取值范围：[1.0, 2.0]
     */
    private Double penaltyScore;

    public Double getTemperature() {
        return temperature;
    }

    public PluginLLM setTemperature(Double temperature) {
        this.temperature = temperature;
        return this;
    }

    public Double getTopP() {
        return topP;
    }

    public PluginLLM setTopP(Double topP) {
        this.topP = topP;
        return this;
    }

    public Double getPenaltyScore() {
        return penaltyScore;
    }

    public PluginLLM setPenaltyScore(Double penaltyScore) {
        this.penaltyScore = penaltyScore;
        return this;
    }
}
