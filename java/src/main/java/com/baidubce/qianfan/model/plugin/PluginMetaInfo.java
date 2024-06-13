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

import java.util.Map;

public class PluginMetaInfo {
    /**
     * 插件名
     */
    private String pluginId;

    /**
     * 原始请求参数
     */
    private Map<String, Object> request;

    /**
     * 原始返回结果
     */
    private Map<String, Object> response;

    public String getPluginId() {
        return pluginId;
    }

    public PluginMetaInfo setPluginId(String pluginId) {
        this.pluginId = pluginId;
        return this;
    }

    public Map<String, Object> getRequest() {
        return request;
    }

    public PluginMetaInfo setRequest(Map<String, Object> request) {
        this.request = request;
        return this;
    }

    public Map<String, Object> getResponse() {
        return response;
    }

    public PluginMetaInfo setResponse(Map<String, Object> response) {
        this.response = response;
        return this;
    }
}
