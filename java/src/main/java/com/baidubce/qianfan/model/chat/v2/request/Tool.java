package com.baidubce.qianfan.model.chat.v2.request;

public class Tool {
    private String type = "function";

    private Function function;

    public String getType() {
        return this.type;
    }

    public Tool setType(String type) {
        this.type = type;
        return this;
    }

    public Function getFunction() {
        return function;
    }

    public Tool setFunction(Function function) {
        this.function = function;
        return this;
    }
}
