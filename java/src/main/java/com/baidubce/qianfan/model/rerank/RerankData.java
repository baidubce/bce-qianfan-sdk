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

package com.baidubce.qianfan.model.rerank;

public class RerankData {
    /**
     * 文本内容
     */
    private String document;

    /**
     * 相似性得分
     */
    private Double relevanceScore;

    /**
     * 序号
     */
    private Integer index;

    public String getDocument() {
        return document;
    }

    public RerankData setDocument(String document) {
        this.document = document;
        return this;
    }

    public Double getRelevanceScore() {
        return relevanceScore;
    }

    public RerankData setRelevanceScore(Double relevanceScore) {
        this.relevanceScore = relevanceScore;
        return this;
    }

    public Integer getIndex() {
        return index;
    }

    public RerankData setIndex(Integer index) {
        this.index = index;
        return this;
    }
}
