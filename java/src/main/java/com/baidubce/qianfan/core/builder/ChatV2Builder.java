package com.baidubce.qianfan.core.builder;

import com.baidubce.qianfan.Qianfan;
import com.baidubce.qianfan.model.chat.V2.*;
import com.baidubce.qianfan.model.chat.V2.request.V2Request;
import com.baidubce.qianfan.model.chat.V2.request.Tool;
import com.baidubce.qianfan.model.chat.V2.request.ToolResult;
import com.baidubce.qianfan.model.chat.V2.response.V2Response;

import java.util.List;
import java.util.Map;

public class ChatV2Builder extends BaseBuilder<ChatV2Builder> {
    private final MessageV2Builder messageBuilder = new MessageV2Builder();

    private String appId;

    private Map<String, Object> streamOptions;

    private Double temperature;

    private Double topP;

    private Double penaltyScore;

    private Integer maxCompletionTokens;

    private Integer seed;

    private List<String> stop;

    private String user;

    private Double frequencyPenalty;

    private Double presencePenalty;

    private List<Tool> tools;

    private Object toolChoice;

    private Boolean parallelToolCalls;

    public ChatV2Builder() {
        super();
    }

    public ChatV2Builder(Qianfan qianfan) {
        super(qianfan);
    }

    public ChatV2Builder addMessage(Message message) {
        this.messageBuilder.add(message);
        return this;
    }

    public ChatV2Builder addMessage(String role, String content) {
        this.messageBuilder.add(role, content);
        return this;
    }

    public ChatV2Builder addUserMessage(String content) {
        this.messageBuilder.addUser(content);
        return this;
    }

    public ChatV2Builder addAssistantMessage(String content) {
        this.messageBuilder.addAssistant(content);
        return this;
    }

    public ChatV2Builder addSystem(String content) {
        this.messageBuilder.addSystem(content);
        return this;
    }

    public ChatV2Builder addToolCalls(List<ToolCall> toolCalls) {
        this.messageBuilder.addToolCalls(toolCalls);
        return this;
    }

    public ChatV2Builder addToolResult(ToolResult toolResult) {
        this.messageBuilder.addToolResult(toolResult);
        return this;
    }

    public ChatV2Builder messages(List<Message> messages) {
        this.messageBuilder.messages(messages);
        return this;
    }

    public ChatV2Builder messages(MessageV2Builder messageBuilder) {
        this.messageBuilder.messages(messageBuilder.build());
        return this;
    }

    public ChatV2Builder toolChoice(Object toolChoice) {
        this.toolChoice = toolChoice;
        return this;
    }

    public ChatV2Builder temperature(Double temperature) {
        this.temperature = temperature;
        return this;
    }

    public ChatV2Builder topP(Double topP) {
        this.topP = topP;
        return this;
    }

    public ChatV2Builder parallelToolCalls(Boolean parallelToolCalls) {
        this.parallelToolCalls = parallelToolCalls;
        return this;
    }

    public ChatV2Builder tools(List<Tool> tools) {
        this.tools = tools;
        return this;
    }

    public ChatV2Builder presencePenalty(Double presencePenalty) {
        this.presencePenalty = presencePenalty;
        return this;
    }

    public ChatV2Builder frequencyPenalty(Double frequencyPenalty) {
        this.frequencyPenalty = frequencyPenalty;
        return this;
    }

    public ChatV2Builder user(String user) {
        this.user = user;
        return this;
    }

    public ChatV2Builder stop(List<String> stop) {
        this.stop = stop;
        return this;
    }

    public ChatV2Builder seed(Integer seed) {
        this.seed = seed;
        return this;
    }

    public ChatV2Builder maxCompletionTokens(Integer maxCompletionTokens) {
        this.maxCompletionTokens = maxCompletionTokens;
        return this;
    }

    public ChatV2Builder penaltyScore(Double penaltyScore) {
        this.penaltyScore = penaltyScore;
        return this;
    }

    public ChatV2Builder streamOptions(Map<String, Object> streamOptions) {
        this.streamOptions = streamOptions;
        return this;
    }

    public ChatV2Builder appId(String appId) {
        this.appId = appId;
        return this;
    }

    public V2Request build() {
        List<Message> messages = messageBuilder.build();
        return new V2Request()
                .setModel(getModel())
                .setMessages(messages)
                .setAppId(appId)
                .setStreamOptions(streamOptions)
                .setTemperature(temperature)
                .setTopP(topP)
                .setPenaltyScore(penaltyScore)
                .setMaxCompletionTokens(maxCompletionTokens)
                .setSeed(seed)
                .setStop(stop)
                .setUser(user)
                .setFrequencyPenalty(frequencyPenalty)
                .setPresencePenalty(presencePenalty)
                .setTools(tools)
                .setToolChoice(toolChoice)
                .setParallelToolCalls(parallelToolCalls);
    }

    public V2Response execute() {
        return super.getQianfan().chatCompletionV2(build());
    }
}
