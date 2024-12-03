package com.baidubce.qianfan.model.chat.v2;

import com.baidubce.qianfan.model.chat.v2.response.Function;

public class ToolCall {

    private String type = "function";

    private String id;

    private Function function;

    public String getType() {
        return this.type;
    }

    public ToolCall setType(String type) {
        this.type = type;
        return this;
    }

    public String getId() {
        return id;
    }

    public ToolCall setId(String id) {
        this.id = id;
        return this;
    }

    public Function getFunction() {
        return function;
    }

    public ToolCall setFunction(Function function) {
        this.function = function;
        return this;
    }
}
