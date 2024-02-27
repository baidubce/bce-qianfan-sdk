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

public class ChatRequest {
    /**
     * 聊天上下文信息
     */
    private List<Message> messages;

    /**
     * 较高的数值会使输出更加随机，而较低的数值会使其更加集中和确定，范围 (0, 1.0]，不能为0
     */
    private Double temperature;

    /**
     * 影响输出文本的多样性，取值越大，生成文本的多样性越强。取值范围 [0, 1.0]
     */
    private Double topP;

    /**
     * 通过对已生成的token增加惩罚，减少重复生成的现象。说明：值越大表示惩罚越大，取值范围：[1.0, 2.0]
     */
    private Double penaltyScore;

    /**
     * 模型人设，主要用于人设设定
     */
    private String system;

    /**
     * 生成停止标识，当模型生成结果以stop中某个元素结尾时，停止文本生成
     */
    private List<String> stop;

    /**
     * 是否强制关闭实时搜索功能
     */
    private Boolean disableSearch;

    /**
     * 是否开启上角标返回
     */
    private Boolean enableCitation;

    /**
     * 指定模型最大输出token数
     */
    private Integer maxOutputTokens;

    /**
     * 指定响应内容的格式
     */
    private String responseFormat;

    /**
     * 表示最终用户的唯一标识符
     */
    private String userId;

    /**
     * 一个可触发函数的描述列表
     */
    private List<Function> functions;

    /**
     * 在函数调用场景下，提示大模型选择指定的函数
     */
    private ToolChoice toolChoice;

    /**
     * 是否为流式请求
     */
    private Boolean stream;

    public List<Message> getMessages() {
        return messages;
    }

    public ChatRequest setMessages(List<Message> messages) {
        this.messages = messages;
        return this;
    }

    public Double getTemperature() {
        return temperature;
    }

    public ChatRequest setTemperature(Double temperature) {
        this.temperature = temperature;
        return this;
    }

    public Double getTopP() {
        return topP;
    }

    public ChatRequest setTopP(Double topP) {
        this.topP = topP;
        return this;
    }

    public Double getPenaltyScore() {
        return penaltyScore;
    }

    public ChatRequest setPenaltyScore(Double penaltyScore) {
        this.penaltyScore = penaltyScore;
        return this;
    }

    public String getSystem() {
        return system;
    }

    public ChatRequest setSystem(String system) {
        this.system = system;
        return this;
    }

    public List<String> getStop() {
        return stop;
    }

    public ChatRequest setStop(List<String> stop) {
        this.stop = stop;
        return this;
    }

    public Boolean getDisableSearch() {
        return disableSearch;
    }

    public ChatRequest setDisableSearch(Boolean disableSearch) {
        this.disableSearch = disableSearch;
        return this;
    }

    public Boolean getEnableCitation() {
        return enableCitation;
    }

    public ChatRequest setEnableCitation(Boolean enableCitation) {
        this.enableCitation = enableCitation;
        return this;
    }

    public Integer getMaxOutputTokens() {
        return maxOutputTokens;
    }

    public ChatRequest setMaxOutputTokens(Integer maxOutputTokens) {
        this.maxOutputTokens = maxOutputTokens;
        return this;
    }

    public String getResponseFormat() {
        return responseFormat;
    }

    public ChatRequest setResponseFormat(String responseFormat) {
        this.responseFormat = responseFormat;
        return this;
    }

    public String getUserId() {
        return userId;
    }

    public ChatRequest setUserId(String userId) {
        this.userId = userId;
        return this;
    }

    public List<Function> getFunctions() {
        return functions;
    }

    public ChatRequest setFunctions(List<Function> functions) {
        this.functions = functions;
        return this;
    }

    public ToolChoice getToolChoice() {
        return toolChoice;
    }

    public ChatRequest setToolChoice(ToolChoice toolChoice) {
        this.toolChoice = toolChoice;
        return this;
    }

    public Boolean getStream() {
        return stream;
    }

    public ChatRequest setStream(Boolean stream) {
        this.stream = stream;
        return this;
    }
}
