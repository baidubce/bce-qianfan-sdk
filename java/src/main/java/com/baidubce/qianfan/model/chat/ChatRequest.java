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

package com.baidubce.qianfan.model.chat;

import com.baidubce.qianfan.model.BaseRequest;
import com.baidubce.qianfan.model.constant.ModelType;

import java.util.List;

public class ChatRequest extends BaseRequest<ChatRequest> {
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
     * 是否开启系统记忆，说明：
     * （1）false：未开启，默认false
     * （2）true：表示开启，开启后，system_memory_id字段必填
     */
    private Boolean enableSystemMemory;

    /**
     * 系统记忆ID，用于读取对应ID下的系统记忆，读取到的记忆文本内容会拼接message参与请求推理
     */
    private String systemMemoryId;

    /**
     * 模型人设，主要用于人设设定
     */
    private String system;

    /**
     * 是否开启用户记忆，非必填字段，默认false
     * 开启后user_id字段为必填字段
     */
    private Boolean enableUserMemory;

    /**
     * 用户记忆召回强度，数值越大，记忆召回强度越高
     * 取值范围[0,4]，默认为1
     */
    private Integer userMemoryLevel;

    /**
     * 用户记忆抽取级别
     * 0：关闭抽取
     * 1：实时抽取-普通抽取
     * 2：实时抽取-高级抽取
     */
    private Integer userMemoryExtractLevel;

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
     * 是否返回搜索溯源信息，说明：
     * （1）如果开启，在触发了搜索增强的场景下，会返回搜索溯源信息search_info，search_info内容见响应参数介绍
     * （2）默认false，表示不开启
     */
    private Boolean enableTrace;

    /**
     * 返回搜索溯源信息的数量
     */
    private Integer traceNumber;

    /**
     * 指定模型最大输出token数
     */
    private Integer maxOutputTokens;

    /**
     * 指定响应内容的格式
     */
    private String responseFormat;

    /**
     * 指定响应内容的风格，当前支持
     * * concise，简洁模式
     * * detailed，详细模式
     */
    private String responseStyle;

    /**
     * 一个可触发函数的描述列表
     */
    private List<Function> functions;

    /**
     * 调用模式，默认为空，当前支持：
     * "speed": 使用极速模式，优化链路耗时，模型效果可能会有影响
     */
    private String mode;

    /**
     * 在函数调用场景下，提示大模型选择指定的函数
     */
    private ToolChoice toolChoice;

    /**
     * 是否为流式请求
     */
    private Boolean stream;

    /**
     * 安全等级
     */
    private String safetyLevel;

    @Override
    public String getType() {
        return ModelType.CHAT;
    }

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

    public Boolean getEnableSystemMemory() {
        return enableSystemMemory;
    }

    public ChatRequest setEnableSystemMemory(Boolean enableSystemMemory) {
        this.enableSystemMemory = enableSystemMemory;
        return this;
    }

    public String getSystemMemoryId() {
        return systemMemoryId;
    }

    public ChatRequest setSystemMemoryId(String systemMemoryId) {
        this.systemMemoryId = systemMemoryId;
        return this;
    }

    public String getSystem() {
        return system;
    }

    public ChatRequest setSystem(String system) {
        this.system = system;
        return this;
    }

    public Boolean getEnableUserMemory() {
        return enableUserMemory;
    }

    public ChatRequest setEnableUserMemory(Boolean enableUserMemory) {
        this.enableUserMemory = enableUserMemory;
        return this;
    }

    public Integer getUserMemoryLevel() {
        return userMemoryLevel;
    }

    public ChatRequest setUserMemoryLevel(Integer userMemoryLevel) {
        this.userMemoryLevel = userMemoryLevel;
        return this;
    }

    public Integer getUserMemoryExtractLevel() {
        return userMemoryExtractLevel;
    }

    public ChatRequest setUserMemoryExtractLevel(Integer userMemoryExtractLevel) {
        this.userMemoryExtractLevel = userMemoryExtractLevel;
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

    public Boolean getEnableTrace() {
        return enableTrace;
    }

    public ChatRequest setEnableTrace(Boolean enableTrace) {
        this.enableTrace = enableTrace;
        return this;
    }

    public Integer getTraceNumber() {
        return traceNumber;
    }

    public ChatRequest setTraceNumber(Integer traceNumber) {
        this.traceNumber = traceNumber;
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

    public String getResponseStyle() {
        return responseStyle;
    }

    public ChatRequest setResponseStyle(String responseStyle) {
        this.responseStyle = responseStyle;
        return this;
    }

    public String getMode() {
        return mode;
    }

    public ChatRequest setMode(String mode) {
        this.mode = mode;
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

    public String getSafetyLevel() {
        return safetyLevel;
    }

    public ChatRequest setSafetyLevel(String safetyLevel) {
        this.safetyLevel = safetyLevel;
        return this;
    }
}
