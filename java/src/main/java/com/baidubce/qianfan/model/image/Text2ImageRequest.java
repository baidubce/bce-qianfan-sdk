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

package com.baidubce.qianfan.model.image;

import com.baidubce.qianfan.model.BaseRequest;

public class Text2ImageRequest extends BaseRequest<Text2ImageRequest> {
    /**
     * 提示词
     * 即用户希望图片包含的元素。长度限制为1024字符，建议中文或者英文单词总数量不超过150个
     */
    private String prompt;

    /**
     * 反向提示词
     * 即用户希望图片不包含的元素。长度限制为1024字符，建议中文或者英文单词总数量不超过150个
     */
    private String negativePrompt;

    /**
     * 生成图片长宽
     * 默认值 1024x1024，取值范围: ["768x768", "768x1024", "1024x768", "576x1024", "1024x576", "1024x1024"]
     */
    private String size;

    /**
     * 生成图片数量，
     * 默认值为1，取值范围为1-4
     */
    private Integer n;

    /**
     * 迭代轮次，默认值为20，取值范围为10-50
     */
    private Integer steps;

    /**
     * 采样方式，默认值为"Euler a"
     */
    private String samplerIndex;

    /**
     * 随机种子，默认自动生成随机数，取值范围 [0, 4294967295]
     */
    private Long seed;

    /**
     * 提示词相关性，默认值为5，取值范围0-30
     */
    private Double cfgScale;

    /**
     * 生成风格，默认值为Base
     */
    private String style;

    public String getPrompt() {
        return prompt;
    }

    public Text2ImageRequest setPrompt(String prompt) {
        this.prompt = prompt;
        return this;
    }

    public String getNegativePrompt() {
        return negativePrompt;
    }

    public Text2ImageRequest setNegativePrompt(String negativePrompt) {
        this.negativePrompt = negativePrompt;
        return this;
    }

    public String getSize() {
        return size;
    }

    public Text2ImageRequest setSize(String size) {
        this.size = size;
        return this;
    }

    public Integer getN() {
        return n;
    }

    public Text2ImageRequest setN(Integer n) {
        this.n = n;
        return this;
    }

    public Integer getSteps() {
        return steps;
    }

    public Text2ImageRequest setSteps(Integer steps) {
        this.steps = steps;
        return this;
    }

    public String getSamplerIndex() {
        return samplerIndex;
    }

    public Text2ImageRequest setSamplerIndex(String samplerIndex) {
        this.samplerIndex = samplerIndex;
        return this;
    }

    public Long getSeed() {
        return seed;
    }

    public Text2ImageRequest setSeed(Long seed) {
        this.seed = seed;
        return this;
    }

    public Double getCfgScale() {
        return cfgScale;
    }

    public Text2ImageRequest setCfgScale(Double cfgScale) {
        this.cfgScale = cfgScale;
        return this;
    }

    public String getStyle() {
        return style;
    }

    public Text2ImageRequest setStyle(String style) {
        this.style = style;
        return this;
    }
}
