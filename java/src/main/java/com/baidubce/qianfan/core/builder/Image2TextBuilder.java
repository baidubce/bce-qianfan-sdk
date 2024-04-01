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
import com.baidubce.qianfan.model.image.Image2TextRequest;
import com.baidubce.qianfan.model.image.Image2TextResponse;

import java.util.Iterator;
import java.util.List;

public class Image2TextBuilder extends BaseBuilder<Image2TextBuilder> {
    private String prompt;

    private String image;

    private Boolean stream;

    private Double temperature;

    private Integer topK;

    private Double topP;

    private Double penaltyScore;

    private List<String> stop;

    public Image2TextBuilder() {
        super();
    }

    public Image2TextBuilder(Qianfan qianfan) {
        super(qianfan);
    }

    public String getPrompt() {
        return prompt;
    }

    public Image2TextBuilder prompt(String prompt) {
        this.prompt = prompt;
        return this;
    }

    public String getImage() {
        return image;
    }

    public Image2TextBuilder image(String image) {
        this.image = image;
        return this;
    }

    public Boolean getStream() {
        return stream;
    }

    public Image2TextBuilder stream(Boolean stream) {
        this.stream = stream;
        return this;
    }

    public Double getTemperature() {
        return temperature;
    }

    public Image2TextBuilder temperature(Double temperature) {
        this.temperature = temperature;
        return this;
    }

    public Integer getTopK() {
        return topK;
    }

    public Image2TextBuilder topK(Integer topK) {
        this.topK = topK;
        return this;
    }

    public Double getTopP() {
        return topP;
    }

    public Image2TextBuilder topP(Double topP) {
        this.topP = topP;
        return this;
    }

    public Double getPenaltyScore() {
        return penaltyScore;
    }

    public Image2TextBuilder penaltyScore(Double penaltyScore) {
        this.penaltyScore = penaltyScore;
        return this;
    }

    public List<String> getStop() {
        return stop;
    }

    public Image2TextBuilder stop(List<String> stop) {
        this.stop = stop;
        return this;
    }

    public Image2TextRequest build() {
        return new Image2TextRequest()
                .setPrompt(prompt)
                .setImage(image)
                .setStream(stream)
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

    public Image2TextResponse execute() {
        return super.getQianfan().image2Text(build());
    }

    public Iterator<Image2TextResponse> executeStream() {
        return super.getQianfan().image2TextStream(build());
    }
}
