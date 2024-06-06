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

import com.baidubce.qianfan.model.BaseRequest;
import com.baidubce.qianfan.model.constant.ModelType;

import java.util.List;
import java.util.Map;

public class PluginRequest extends BaseRequest<PluginRequest> {
    /**
     * 查询信息。说明：
     * （1）成员不能为空
     * （2）长度不能超过1000个字符
     */
    private String query;

    /**
     * 需要调用的插件ID列表，说明：
     * （1）如果使用知识库插件，该字段必填，且固定值为["uuid-zhishiku"]，参数示例："plugins":["uuid-zhishiku"]
     * （2）如果不填写该字段，是在插件编排时配置范围内进行意图识别，使用模型进行回答
     */
    private List<String> plugins;

    /**
     * 文件的URL地址，说明：
     * （1）图片要求是百度BOS上的图片，即用户必须现将图片上传至百度BOS，图片url地址包含bcebos.com；只有在访问北京区域BOS，才不会产生BOS的外网流出流量费用
     * （2）图片支持jpg、jpeg、png，必须带后缀名
     * （3）图像尺寸最小为80*80，如果图像小于该尺寸，则无法识别
     */
    private String fileurl;

    /**
     * 是否以流式接口的形式返回数据，默认false，可选值如下：
     * （1）true: 是，以流式接口的形式返回数据
     * （2）false：否，非流式接口形式返回数据
     */
    private Boolean stream;

    /**
     * lm相关参数，不指定参数时，使用调试过程中的默认值。
     * 参数示例："llm":{"temperature":0.1,"top_p":1,"penalty_score":1}
     */
    private PluginLLM llm;

    /**
     * 说明：
     * （1）如果prompt中使用了变量，推理时可以填写具体值；
     * （2）如果prompt中未使用变量，该字段不填。
     * 参数示例："input_variables"：{"key1":"value1","key2":"value2"}
     * key1、key2为配置时prompt中使用了变量key
     */
    private Map<String, String> inputVariables;

    /**
     * 聊天上下文信息。说明：
     * （1）history可以为空
     * （2）非空情况下数目必须为偶数，奇数位history的role值必须为user，偶数位history的role值为assistant。参数示例：
     * [{"role":"user","content":"..."},{"role":"assistant","content":"..."},...]
     */
    private List<PluginHistory> history;

    /**
     * 是否返回插件的原始请求信息，默认false，可选值如下：
     * true：是，返回插件的原始请求信息meta_info
     * false：否，不返回插件的原始请求信息meta_info
     */
    private Boolean verbose;

    @Override
    public String getType() {
        return ModelType.PLUGIN;
    }

    public String getQuery() {
        return query;
    }

    public PluginRequest setQuery(String query) {
        this.query = query;
        return this;
    }

    public List<String> getPlugins() {
        return plugins;
    }

    public PluginRequest setPlugins(List<String> plugins) {
        this.plugins = plugins;
        return this;
    }

    public String getFileurl() {
        return fileurl;
    }

    public PluginRequest setFileurl(String fileurl) {
        this.fileurl = fileurl;
        return this;
    }

    public Boolean getStream() {
        return stream;
    }

    public PluginRequest setStream(Boolean stream) {
        this.stream = stream;
        return this;
    }

    public PluginLLM getLlm() {
        return llm;
    }

    public PluginRequest setLlm(PluginLLM llm) {
        this.llm = llm;
        return this;
    }

    public Map<String, String> getInputVariables() {
        return inputVariables;
    }

    public PluginRequest setInputVariables(Map<String, String> inputVariables) {
        this.inputVariables = inputVariables;
        return this;
    }

    public List<PluginHistory> getHistory() {
        return history;
    }

    public PluginRequest setHistory(List<PluginHistory> history) {
        this.history = history;
        return this;
    }

    public Boolean getVerbose() {
        return verbose;
    }

    public PluginRequest setVerbose(Boolean verbose) {
        this.verbose = verbose;
        return this;
    }
}
