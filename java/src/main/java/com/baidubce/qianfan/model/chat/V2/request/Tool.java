package com.baidubce.qianfan.model.chat.V2.request;

public class Tool {
    public final String type = "function";

    private Function function;

    public Function getFunction() {
        return function;
    }

    public Tool setFunction(Function function) {
        this.function = function;
        return this;
    }
}
