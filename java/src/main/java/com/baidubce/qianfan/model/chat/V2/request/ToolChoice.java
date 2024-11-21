package com.baidubce.qianfan.model.chat.V2.request;

public class ToolChoice {
    public final String type = "function";

    private Function function;

    public Function getFunction() {
        return function;
    }

    public ToolChoice setFunction(Function function) {
        this.function = function;
        return this;
    }
}
