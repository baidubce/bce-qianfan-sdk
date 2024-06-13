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

public class PluginHistory {
    /**
     * 角色，可选 "user", "assistant"
     */
    private String role;

    /**
     * 对话内容
     */
    private String content;

    public String getRole() {
        return role;
    }

    public PluginHistory setRole(String role) {
        this.role = role;
        return this;
    }

    public String getContent() {
        return content;
    }

    public PluginHistory setContent(String content) {
        this.content = content;
        return this;
    }
}
