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
import com.baidubce.qianfan.core.StreamIterator;
import com.baidubce.qianfan.model.plugin.PluginHistory;
import com.baidubce.qianfan.model.plugin.PluginLLM;
import com.baidubce.qianfan.model.plugin.PluginRequest;
import com.baidubce.qianfan.model.plugin.PluginResponse;

import java.util.Iterator;
import java.util.List;
import java.util.Map;

public class PluginBuilder extends BaseBuilder<PluginBuilder> {
    private String query;

    private List<String> plugins;

    private String fileurl;

    private PluginLLM llm;

    private Map<String, String> inputVariables;

    private List<PluginHistory> history;

    private Boolean verbose;

    public PluginBuilder() {
        super();
    }

    public PluginBuilder(Qianfan qianfan) {
        super(qianfan);
    }

    public PluginBuilder query(String query) {
        this.query = query;
        return this;
    }

    public PluginBuilder plugins(List<String> plugins) {
        this.plugins = plugins;
        return this;
    }

    public PluginBuilder fileurl(String fileurl) {
        this.fileurl = fileurl;
        return this;
    }

    public PluginBuilder llm(PluginLLM llm) {
        this.llm = llm;
        return this;
    }

    public PluginBuilder inputVariables(Map<String, String> inputVariables) {
        this.inputVariables = inputVariables;
        return this;
    }

    public PluginBuilder history(List<PluginHistory> history) {
        this.history = history;
        return this;
    }

    public PluginBuilder verbose(Boolean verbose) {
        this.verbose = verbose;
        return this;
    }

    public PluginRequest build() {
        return new PluginRequest()
                .setQuery(query)
                .setPlugins(plugins)
                .setFileurl(fileurl)
                .setLlm(llm)
                .setInputVariables(inputVariables)
                .setHistory(history)
                .setVerbose(verbose)
                .setEndpoint(super.getEndpoint())
                .setUserId(super.getUserId())
                .setExtraParameters(super.getExtraParameters());
    }

    public PluginResponse execute() {
        return super.getQianfan().plugin(build());
    }

    public StreamIterator<PluginResponse> executeStream() {
        return super.getQianfan().pluginStream(build());
    }
}
