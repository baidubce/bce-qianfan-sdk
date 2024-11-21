package com.baidubce.qianfan.model.chat.V2.request;

import com.baidubce.qianfan.model.BaseRequest;
import com.baidubce.qianfan.model.chat.V2.Message;
import com.baidubce.qianfan.model.constant.ModelType;

import java.util.List;
import java.util.Map;

public class V2Request extends BaseRequest<V2Request> {
    private List<Message> messages;

    private String appId;

    private boolean stream;

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

    @Override
    public String getType() {
        return ModelType.CHAT;
    }

    public List<Message> getMessages() {
        return messages;
    }

    public V2Request setMessages(List<Message> messages) {
        this.messages = messages;
        return this;
    }

    public String getAppId() {
        return appId;
    }

    public V2Request setAppId(String appId) {
        this.appId = appId;
        if (appId != null) {
            this.getHeaders().put("appid", appId);
        }
        return this;
    }

    public boolean isStream() {
        return stream;
    }

    public V2Request setStream(boolean stream) {
        this.stream = stream;
        return this;
    }

    public Map<String, Object> getStreamOptions() {
        return streamOptions;
    }

    public V2Request setStreamOptions(Map<String, Object> streamOptions) {
        this.streamOptions = streamOptions;
        return this;
    }

    public Double getTemperature() {
        return temperature;
    }

    public V2Request setTemperature(Double temperature) {
        this.temperature = temperature;
        return this;
    }

    public Double getTopP() {
        return topP;
    }

    public V2Request setTopP(Double topP) {
        this.topP = topP;
        return this;
    }

    public Double getPenaltyScore() {
        return penaltyScore;
    }

    public V2Request setPenaltyScore(Double penaltyScore) {
        this.penaltyScore = penaltyScore;
        return this;
    }

    public Integer getMaxCompletionTokens() {
        return maxCompletionTokens;
    }

    public V2Request setMaxCompletionTokens(Integer maxCompletionTokens) {
        this.maxCompletionTokens = maxCompletionTokens;
        return this;
    }

    public Integer getSeed() {
        return seed;
    }

    public V2Request setSeed(Integer seed) {
        this.seed = seed;
        return this;
    }

    public List<String> getStop() {
        return stop;
    }

    public V2Request setStop(List<String> stop) {
        this.stop = stop;
        return this;
    }

    public String getUser() {
        return user;
    }

    public V2Request setUser(String user) {
        this.user = user;
        return this;
    }

    public Double getFrequencyPenalty() {
        return frequencyPenalty;
    }

    public V2Request setFrequencyPenalty(Double frequencyPenalty) {
        this.frequencyPenalty = frequencyPenalty;
        return this;
    }

    public Double getPresencePenalty() {
        return presencePenalty;
    }

    public V2Request setPresencePenalty(Double presencePenalty) {
        this.presencePenalty = presencePenalty;
        return this;
    }

    public List<Tool> getTools() {
        return tools;
    }

    public V2Request setTools(List<Tool> tools) {
        this.tools = tools;
        return this;
    }

    public Object getToolChoice() {
        return toolChoice;
    }

    public V2Request setToolChoice(Object toolChoice) {
        this.toolChoice = toolChoice;
        return this;
    }

    public Boolean getParallelToolCalls() {
        return parallelToolCalls;
    }

    public V2Request setParallelToolCalls(Boolean parallelToolCalls) {
        this.parallelToolCalls = parallelToolCalls;
        return this;
    }
}
