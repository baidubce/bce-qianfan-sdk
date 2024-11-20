package com.baidubce.qianfan.model.chat.V2;

import com.baidubce.qianfan.model.BaseRequest;
import com.baidubce.qianfan.model.constant.ModelType;

import java.util.HashMap;
import java.util.List;

public class ChatV2Request extends BaseRequest<ChatV2Request> {
    private List<Message> messages;

    private String appId;

    private HashMap<String, Object> streamOptions;

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

    private RequestToolChoice toolChoice;

    private Boolean parallelToolCalls;

    @Override
    public String getType() {
        return ModelType.CHAT;
    }

    public List<Message> getMessages() {
        return messages;
    }

    public ChatV2Request setMessages(List<Message> messages) {
        this.messages = messages;
        return this;
    }

    public String getAppId() {
        return appId;
    }

    public ChatV2Request setAppId(String appId) {
        this.appId = appId;
        if (appId != null) {
            this.getHeaders().put("appid", appId);
        }
        return this;
    }

    public HashMap<String, Object> getStreamOptions() {
        return streamOptions;
    }

    public ChatV2Request setStreamOptions(HashMap<String, Object> streamOptions) {
        this.streamOptions = streamOptions;
        return this;
    }

    public Double getTemperature() {
        return temperature;
    }

    public ChatV2Request setTemperature(Double temperature) {
        this.temperature = temperature;
        return this;
    }

    public Double getTopP() {
        return topP;
    }

    public ChatV2Request setTopP(Double topP) {
        this.topP = topP;
        return this;
    }

    public Double getPenaltyScore() {
        return penaltyScore;
    }

    public ChatV2Request setPenaltyScore(Double penaltyScore) {
        this.penaltyScore = penaltyScore;
        return this;
    }

    public Integer getMaxCompletionTokens() {
        return maxCompletionTokens;
    }

    public ChatV2Request setMaxCompletionTokens(Integer maxCompletionTokens) {
        this.maxCompletionTokens = maxCompletionTokens;
        return this;
    }

    public Integer getSeed() {
        return seed;
    }

    public ChatV2Request setSeed(Integer seed) {
        this.seed = seed;
        return this;
    }

    public List<String> getStop() {
        return stop;
    }

    public ChatV2Request setStop(List<String> stop) {
        this.stop = stop;
        return this;
    }

    public String getUser() {
        return user;
    }

    public ChatV2Request setUser(String user) {
        this.user = user;
        return this;
    }

    public Double getFrequencyPenalty() {
        return frequencyPenalty;
    }

    public ChatV2Request setFrequencyPenalty(Double frequencyPenalty) {
        this.frequencyPenalty = frequencyPenalty;
        return this;
    }

    public Double getPresencePenalty() {
        return presencePenalty;
    }

    public ChatV2Request setPresencePenalty(Double presencePenalty) {
        this.presencePenalty = presencePenalty;
        return this;
    }

    public List<Tool> getTools() {
        return tools;
    }

    public ChatV2Request setTools(List<Tool> tools) {
        this.tools = tools;
        return this;
    }

    public RequestToolChoice getToolChoice() {
        return toolChoice;
    }

    public ChatV2Request setToolChoice(RequestToolChoice toolChoice) {
        this.toolChoice = toolChoice;
        return this;
    }

    public Boolean getParallelToolCalls() {
        return parallelToolCalls;
    }

    public ChatV2Request setParallelToolCalls(Boolean parallelToolCalls) {
        this.parallelToolCalls = parallelToolCalls;
        return this;
    }
}
