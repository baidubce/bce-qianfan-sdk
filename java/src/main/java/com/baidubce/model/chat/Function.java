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

package com.baidubce.model.chat;

import java.util.List;

public class Function {
    /**
     * 函数名
     */
    private String name;

    /**
     * 函数描述
     */
    private String description;

    /**
     * 函数请求参数
     */
    private Object parameters;

    /**
     * 函数响应参数
     */
    private Object responses;

    /**
     * function调用的一些历史示例
     */
    private List<List<Example>> examples;

    public String getName() {
        return name;
    }

    public Function setName(String name) {
        this.name = name;
        return this;
    }

    public String getDescription() {
        return description;
    }

    public Function setDescription(String description) {
        this.description = description;
        return this;
    }

    public Object getParameters() {
        return parameters;
    }

    public Function setParameters(Object parameters) {
        this.parameters = parameters;
        return this;
    }

    public Object getResponses() {
        return responses;
    }

    public Function setResponses(Object responses) {
        this.responses = responses;
        return this;
    }

    public List<List<Example>> getExamples() {
        return examples;
    }

    public Function setExamples(List<List<Example>> examples) {
        this.examples = examples;
        return this;
    }
}
