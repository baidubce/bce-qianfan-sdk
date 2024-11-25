package com.baidubce.qianfan.core.builder;

import com.baidubce.qianfan.model.chat.v2.Message;
import com.baidubce.qianfan.model.chat.v2.ToolCall;
import com.baidubce.qianfan.model.chat.v2.request.ToolResult;
import com.baidubce.qianfan.model.constant.V2.ChatRole;

import java.util.ArrayList;
import java.util.List;

public class MessageV2Builder {
    private List<Message> messages = new ArrayList<>();

    public MessageV2Builder add(Message message) {
        this.messages.add(message);
        return this;
    }

    public MessageV2Builder add(String role, String content) {
        this.messages.add(new Message()
                .setRole(role)
                .setContent(content)
        );
        return this;
    }

    public MessageV2Builder addUser(String content) {
        this.messages.add(new Message()
                .setRole(ChatRole.USER)
                .setContent(content)
        );
        return this;
    }

    public MessageV2Builder addAssistant(String content) {
        this.messages.add(new Message()
                .setRole(ChatRole.ASSISTANT)
                .setContent(content)
        );
        return this;
    }

    public MessageV2Builder addSystem(String content) {
        this.messages.add(new Message()
                .setRole(ChatRole.SYSTEM)
                .setContent(content)
        );
        return this;
    }

    public MessageV2Builder addToolCalls(List<ToolCall> toolCalls) {
        this.messages.add(new Message()
                .setRole(ChatRole.ASSISTANT)
                .setToolCalls(toolCalls)
        );
        return this;
    }

    public MessageV2Builder addToolResult(ToolResult toolResult) {
        this.messages.add(new Message()
                .setRole(ChatRole.TOOL)
                .setName(toolResult.getToolName())
                .setToolCallId(toolResult.getToolCallId())
                .setContent(toolResult.getContent())
        );

        return this;
    }

    public MessageV2Builder messages(List<Message> messages) {
        this.messages = messages;
        return this;
    }

    public List<Message> build() {
        return messages;
    }
}
