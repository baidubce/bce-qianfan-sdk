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

public class FunctionCall {
    /**
     * 触发的function名
     */
    private String name;

    /**
     * 请求参数
     */
    private String arguments;

    /**
     * 模型思考过程
     */
    private String thoughts;

    public String getName() {
        return name;
    }

    public FunctionCall setName(String name) {
        this.name = name;
        return this;
    }

    public String getArguments() {
        return arguments;
    }

    public FunctionCall setArguments(String arguments) {
        this.arguments = arguments;
        return this;
    }

    public String getThoughts() {
        return thoughts;
    }

    public FunctionCall setThoughts(String thoughts) {
        this.thoughts = thoughts;
        return this;
    }
}
