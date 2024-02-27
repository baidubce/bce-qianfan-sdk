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

package com.baidubce.model.embedding;

import java.math.BigDecimal;
import java.util.List;

public class EmbeddingData {
    /**
     * 固定值"embedding"
     */
    private String object;

    /**
     * embedding 内容
     */
    private List<BigDecimal> embedding;

    /**
     * 序号
     */
    private Integer index;

    public String getObject() {
        return object;
    }

    public EmbeddingData setObject(String object) {
        this.object = object;
        return this;
    }

    public List<BigDecimal> getEmbedding() {
        return embedding;
    }

    public EmbeddingData setEmbedding(List<BigDecimal> embedding) {
        this.embedding = embedding;
        return this;
    }

    public Integer getIndex() {
        return index;
    }

    public EmbeddingData setIndex(Integer index) {
        this.index = index;
        return this;
    }
}
