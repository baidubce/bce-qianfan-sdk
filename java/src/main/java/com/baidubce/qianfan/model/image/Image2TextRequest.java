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
import com.baidubce.qianfan.model.constant.ModelType;

import java.util.List;

public class Image2TextRequest extends BaseRequest<Image2TextRequest> {
    /**
     * 提示词
     */
    private String prompt;

    /**
     * 图片数据
     * base64编码，要求base64编码后大小不超过4M，最短边至少15px，最长边最大4096px，支持jpg/png/bmp格式，注意请去掉头部
     */
    private String image;

    /**
     * 是否以流式接口的形式返回数据，默认false
     */
    private Boolean stream;

    /**
     * 说明：
     * （1）较高的数值会使输出更加随机，而较低的数值会使其更加集中和确定
     * （2）范围 (0, 1.0]，不能为0
     */
    private Double temperature;

    /**
     * Top-K 采样参数，在每轮token生成时，保留k个概率最高的token作为候选。说明：
     * （1）影响输出文本的多样性，取值越大，生成文本的多样性越强
     * （2）取值范围：正整数
     */
    private Integer topK;

    /**
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

    /**
     * 生成停止标识。当模型生成结果以stop中某个元素结尾时，停止文本生成。说明：
     * （1）每个元素长度不超过20字符。
     * （2）最多4个元素
     */
    private List<String> stop;

    @Override
    public String getType() {
        return ModelType.IMAGE_2_TEXT;
    }

    public String getPrompt() {
        return prompt;
    }

    public Image2TextRequest setPrompt(String prompt) {
        this.prompt = prompt;
        return this;
    }


    public String getImage() {
        return image;
    }

    public Image2TextRequest setImage(String image) {
        this.image = image;
        return this;
    }

    public Boolean getStream() {
        return stream;
    }

    public Image2TextRequest setStream(Boolean stream) {
        this.stream = stream;
        return this;
    }

    public Double getTemperature() {
        return temperature;
    }

    public Image2TextRequest setTemperature(Double temperature) {
        this.temperature = temperature;
        return this;
    }

    public Integer getTopK() {
        return topK;
    }

    public Image2TextRequest setTopK(Integer topK) {
        this.topK = topK;
        return this;
    }

    public Double getTopP() {
        return topP;
    }

    public Image2TextRequest setTopP(Double topP) {
        this.topP = topP;
        return this;
    }

    public Double getPenaltyScore() {
        return penaltyScore;
    }

    public Image2TextRequest setPenaltyScore(Double penaltyScore) {
        this.penaltyScore = penaltyScore;
        return this;
    }

    public List<String> getStop() {
        return stop;
    }

    public Image2TextRequest setStop(List<String> stop) {
        this.stop = stop;
        return this;
    }
}
