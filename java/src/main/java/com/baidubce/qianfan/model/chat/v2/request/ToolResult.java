package com.baidubce.qianfan.model.chat.v2.request;

public class ToolResult {
    private String toolName;

    private String toolCallId;

    private String content;

    public String getToolName() {
        return toolName;
    }

    public ToolResult setToolName(String toolName) {
        this.toolName = toolName;
        return this;
    }

    public String getToolCallId() {
        return toolCallId;
    }

    public ToolResult setToolCallId(String toolCallId) {
        this.toolCallId = toolCallId;
        return this;
    }

    public String getContent() {
        return content;
    }

    public ToolResult setContent(String content) {
        this.content = content;
        return this;
    }
}
