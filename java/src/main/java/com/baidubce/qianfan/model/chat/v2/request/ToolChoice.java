package com.baidubce.qianfan.model.chat.v2.request;

public class ToolChoice {
    private String type = "function";

    private Function function;

    public String getType() {
        return this.type;
    }

    public ToolChoice setType(String type) {
        this.type = type;
        return this;
    }

    public Function getFunction() {
        return function;
    }

    public ToolChoice setFunction(Function function) {
        this.function = function;
        return this;
    }
}
