package com.baidubce.qianfan.model.chat.v2;

import com.google.gson.annotations.SerializedName;

import java.util.List;

public class Message {

    private String role;

    private String name;

    private String content;

    @SerializedName("tool_calls")
    private List<ToolCall> toolCalls;

    @SerializedName("tool_call_id")
    private String toolCallId;

    public String getRole() {
        return role;
    }

    public Message setRole(String role) {
        this.role = role;
        return this;
    }

    public String getName() {
        return name;
    }

    public Message setName(String name) {
        this.name = name;
        return this;
    }

    public String getContent() {
        return content;
    }

    public Message setContent(String content) {
        this.content = content;
        return this;
    }

    public List<ToolCall> getToolCalls() {
        return toolCalls;
    }

    public Message setToolCalls(List<ToolCall> toolCalls) {
        this.toolCalls = toolCalls;
        return this;
    }

    public String getToolCallId() {
        return toolCallId;
    }

    public Message setToolCallId(String toolCallId) {
        this.toolCallId = toolCallId;
        return this;
    }
}
