package com.baidubce.qianfan.model.chat.v2.request;

import com.baidubce.qianfan.model.BaseRequest;
import com.baidubce.qianfan.model.chat.v2.Message;
import com.baidubce.qianfan.model.constant.ModelType;

import java.util.List;
import java.util.Map;

public class RequestV2 extends BaseRequest<RequestV2> {
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

    public RequestV2 setMessages(List<Message> messages) {
        this.messages = messages;
        return this;
    }

    public String getAppId() {
        return appId;
    }

    public RequestV2 setAppId(String appId) {
        this.appId = appId;
        if (appId != null) {
            this.getHeaders().put("appid", appId);
        }
        return this;
    }

    public boolean isStream() {
        return stream;
    }

    public RequestV2 setStream(boolean stream) {
        this.stream = stream;
        return this;
    }

    public Map<String, Object> getStreamOptions() {
        return streamOptions;
    }

    public RequestV2 setStreamOptions(Map<String, Object> streamOptions) {
        this.streamOptions = streamOptions;
        return this;
    }

    public Double getTemperature() {
        return temperature;
    }

    public RequestV2 setTemperature(Double temperature) {
        this.temperature = temperature;
        return this;
    }

    public Double getTopP() {
        return topP;
    }

    public RequestV2 setTopP(Double topP) {
        this.topP = topP;
        return this;
    }

    public Double getPenaltyScore() {
        return penaltyScore;
    }

    public RequestV2 setPenaltyScore(Double penaltyScore) {
        this.penaltyScore = penaltyScore;
        return this;
    }

    public Integer getMaxCompletionTokens() {
        return maxCompletionTokens;
    }

    public RequestV2 setMaxCompletionTokens(Integer maxCompletionTokens) {
        this.maxCompletionTokens = maxCompletionTokens;
        return this;
    }

    public Integer getSeed() {
        return seed;
    }

    public RequestV2 setSeed(Integer seed) {
        this.seed = seed;
        return this;
    }

    public List<String> getStop() {
        return stop;
    }

    public RequestV2 setStop(List<String> stop) {
        this.stop = stop;
        return this;
    }

    public String getUser() {
        return user;
    }

    public RequestV2 setUser(String user) {
        this.user = user;
        return this;
    }

    public Double getFrequencyPenalty() {
        return frequencyPenalty;
    }

    public RequestV2 setFrequencyPenalty(Double frequencyPenalty) {
        this.frequencyPenalty = frequencyPenalty;
        return this;
    }

    public Double getPresencePenalty() {
        return presencePenalty;
    }

    public RequestV2 setPresencePenalty(Double presencePenalty) {
        this.presencePenalty = presencePenalty;
        return this;
    }

    public List<Tool> getTools() {
        return tools;
    }

    public RequestV2 setTools(List<Tool> tools) {
        this.tools = tools;
        return this;
    }

    public Object getToolChoice() {
        return toolChoice;
    }

    public RequestV2 setToolChoice(Object toolChoice) {
        this.toolChoice = toolChoice;
        return this;
    }

    public Boolean getParallelToolCalls() {
        return parallelToolCalls;
    }

    public RequestV2 setParallelToolCalls(Boolean parallelToolCalls) {
        this.parallelToolCalls = parallelToolCalls;
        return this;
    }
}
