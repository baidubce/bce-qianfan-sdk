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

import com.baidubce.qianfan.model.chat.FunctionCall;
import com.baidubce.qianfan.model.chat.Message;
import com.baidubce.qianfan.model.constant.ChatRole;

import java.util.ArrayList;
import java.util.List;

public class MessageBuilder {
    private List<Message> messages = new ArrayList<>();

    public MessageBuilder add(Message message) {
        this.messages.add(message);
        return this;
    }

    public MessageBuilder add(String role, String content) {
        this.messages.add(new Message()
                .setRole(role)
                .setContent(content)
        );
        return this;
    }

    public MessageBuilder addUser(String content) {
        this.messages.add(new Message()
                .setRole(ChatRole.USER)
                .setContent(content)
        );
        return this;
    }

    public MessageBuilder addAssistant(String content) {
        this.messages.add(new Message()
                .setRole(ChatRole.ASSISTANT)
                .setContent(content)
        );
        return this;
    }

    public MessageBuilder addFunctionCall(FunctionCall functionCall) {
        this.messages.add(new Message()
                .setRole(ChatRole.ASSISTANT)
                .setFunctionCall(functionCall)
        );
        return this;
    }

    public MessageBuilder addFunctionCallResult(String name, String content) {
        this.messages.add(new Message()
                .setRole(ChatRole.FUNCTION)
                .setName(name)
                .setContent(content)
        );
        return this;
    }

    public MessageBuilder messages(List<Message> messages) {
        this.messages = messages;
        return this;
    }

    public List<Message> build() {
        return messages;
    }
}
