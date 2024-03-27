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
import com.baidubce.qianfan.model.chat.*;

import java.util.Iterator;
import java.util.List;

public class ChatBuilder extends BaseBuilder<ChatBuilder> {
    private final MessageBuilder messageBuilder = new MessageBuilder();

    private Double temperature;

    private Double topP;

    private Double penaltyScore;

    private String system;

    private List<String> stop;

    private Boolean disableSearch;

    private Boolean enableCitation;

    private Integer maxOutputTokens;

    private String responseFormat;

    private List<Function> functions;

    private ToolChoice toolChoice;

    public ChatBuilder() {
        super();
    }

    public ChatBuilder(Qianfan qianfan) {
        super(qianfan);
    }

    public ChatBuilder addMessage(Message message) {
        this.messageBuilder.add(message);
        return this;
    }

    public ChatBuilder addMessage(String role, String content) {
        this.messageBuilder.add(role, content);
        return this;
    }

    public ChatBuilder addUserMessage(String content) {
        this.messageBuilder.addUser(content);
        return this;
    }

    public ChatBuilder addAssistantMessage(String content) {
        this.messageBuilder.addAssistant(content);
        return this;
    }

    public ChatBuilder addFunctionCallMessage(FunctionCall functionCall) {
        this.messageBuilder.addFunctionCall(functionCall);
        return this;
    }

    public ChatBuilder addFunctionCallResultMessage(String name, String content) {
        this.messageBuilder.addFunctionCallResult(name, content);
        return this;
    }

    public ChatBuilder messages(MessageBuilder messages) {
        this.messageBuilder.messages(messages.build());
        return this;
    }

    public ChatBuilder messages(List<Message> messages) {
        this.messageBuilder.messages(messages);
        return this;
    }

    public ChatBuilder temperature(Double temperature) {
        this.temperature = temperature;
        return this;
    }

    public ChatBuilder topP(Double topP) {
        this.topP = topP;
        return this;
    }

    public ChatBuilder penaltyScore(Double penaltyScore) {
        this.penaltyScore = penaltyScore;
        return this;
    }

    public ChatBuilder system(String system) {
        this.system = system;
        return this;
    }

    public ChatBuilder stop(List<String> stop) {
        this.stop = stop;
        return this;
    }

    public ChatBuilder disableSearch(Boolean disableSearch) {
        this.disableSearch = disableSearch;
        return this;
    }

    public ChatBuilder enableCitation(Boolean enableCitation) {
        this.enableCitation = enableCitation;
        return this;
    }

    public ChatBuilder maxOutputTokens(Integer maxOutputTokens) {
        this.maxOutputTokens = maxOutputTokens;
        return this;
    }

    public ChatBuilder responseFormat(String responseFormat) {
        this.responseFormat = responseFormat;
        return this;
    }

    public ChatBuilder functions(List<Function> functions) {
        this.functions = functions;
        return this;
    }

    public ChatBuilder toolChoice(ToolChoice toolChoice) {
        this.toolChoice = toolChoice;
        return this;
    }

    public ChatRequest build() {
        List<Message> messages = messageBuilder.build();
        return new ChatRequest()
                .setMessages(messages)
                .setTemperature(temperature)
                .setTopP(topP)
                .setPenaltyScore(penaltyScore)
                .setSystem(system)
                .setStop(stop)
                .setDisableSearch(disableSearch)
                .setEnableCitation(enableCitation)
                .setMaxOutputTokens(maxOutputTokens)
                .setResponseFormat(responseFormat)
                .setFunctions(functions)
                .setToolChoice(toolChoice)
                .setModel(super.getModel())
                .setEndpoint(super.getEndpoint())
                .setUserId(super.getUserId())
                .setExtraParameters(super.getExtraParameters());
    }

    public ChatResponse execute() {
        return super.getQianfan().chatCompletion(build());
    }

    public Iterator<ChatResponse> executeStream() {
        return super.getQianfan().chatCompletionStream(build());
    }
}
