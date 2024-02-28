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

import java.util.List;

public class EmbeddingRequest {
    /**
     * 模型的调用端点
     */
    private String endpoint;

    /**
     * 输入文本以获取embedding
     */
    private List<String> input;

    /**
     * 表示最终用户的唯一标识符
     */
    private String userId;

    public String getEndpoint() {
        return endpoint;
    }

    public EmbeddingRequest setEndpoint(String endpoint) {
        this.endpoint = endpoint;
        return this;
    }

    public List<String> getInput() {
        return input;
    }

    public EmbeddingRequest setInput(List<String> input) {
        this.input = input;
        return this;
    }

    public String getUserId() {
        return userId;
    }

    public EmbeddingRequest setUserId(String userId) {
        this.userId = userId;
        return this;
    }
}
