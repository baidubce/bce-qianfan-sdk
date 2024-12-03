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
import com.baidubce.qianfan.model.image.Text2ImageRequest;
import com.baidubce.qianfan.model.image.Text2ImageResponse;

public class Text2ImageBuilder extends BaseBuilderV1<Text2ImageBuilder> {
    private String prompt;

    private String negativePrompt;

    private String size;

    private Integer n;

    private Integer steps;

    private String samplerIndex;

    private Long seed;

    private Double cfgScale;

    private String style;

    public Text2ImageBuilder() {
        super();
    }

    public Text2ImageBuilder(Qianfan qianfan) {
        super(qianfan);
    }

    public Text2ImageBuilder prompt(String prompt) {
        this.prompt = prompt;
        return this;
    }

    public Text2ImageBuilder negativePrompt(String negativePrompt) {
        this.negativePrompt = negativePrompt;
        return this;
    }

    public Text2ImageBuilder size(String size) {
        this.size = size;
        return this;
    }

    public Text2ImageBuilder n(Integer n) {
        this.n = n;
        return this;
    }

    public Text2ImageBuilder steps(Integer steps) {
        this.steps = steps;
        return this;
    }

    public Text2ImageBuilder samplerIndex(String samplerIndex) {
        this.samplerIndex = samplerIndex;
        return this;
    }

    public Text2ImageBuilder seed(Long seed) {
        this.seed = seed;
        return this;
    }

    public Text2ImageBuilder cfgScale(Double cfgScale) {
        this.cfgScale = cfgScale;
        return this;
    }

    public Text2ImageBuilder style(String style) {
        this.style = style;
        return this;
    }

    public Text2ImageRequest build() {
        return new Text2ImageRequest()
                .setPrompt(prompt)
                .setNegativePrompt(negativePrompt)
                .setSize(size)
                .setN(n)
                .setSteps(steps)
                .setSamplerIndex(samplerIndex)
                .setSeed(seed)
                .setCfgScale(cfgScale)
                .setStyle(style)
                .setModel(super.getModel())
                .setEndpoint(super.getEndpoint())
                .setUserId(super.getUserId())
                .setExtraParameters(super.getExtraParameters());
    }

    public Text2ImageResponse execute() {
        return super.getQianfan().text2Image(build());
    }
}
