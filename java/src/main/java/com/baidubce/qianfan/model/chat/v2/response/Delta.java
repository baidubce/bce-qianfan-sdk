package com.baidubce.qianfan.model.chat.v2.response;

import com.baidubce.qianfan.model.chat.v2.ToolCall;
import com.google.gson.annotations.SerializedName;

import java.util.List;

public class Delta {
    private String content;

    @SerializedName("reasoning_content")
    private String reasoningContent;

    @SerializedName("tool_calls")
    private List<ToolCall> toolCalls;

    public String getContent() {
        return content;
    }

    public Delta setContent(String content) {
        this.content = content;
        return this;
    }


    public String getReasoningContent() {
        return reasoningContent;
    }

    public Delta setReasoningContent(String reasoningContent) {
        this.reasoningContent = reasoningContent;
        return this;
    }

    public List<ToolCall> getToolCalls() {
        return toolCalls;
    }

    public Delta setToolCalls(List<ToolCall> toolCalls) {
        this.toolCalls = toolCalls;
        return this;
    }
}
