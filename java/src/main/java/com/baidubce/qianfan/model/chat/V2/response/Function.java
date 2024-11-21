package com.baidubce.qianfan.model.chat.V2.response;

public class Function {
    private String name;

    private String arguments;

    public String getName() {
        return name;
    }

    public Function setName(String name) {
        this.name = name;
        return this;
    }

    public String getArguments() {
        return arguments;
    }

    public Function setArguments(String arguments) {
        this.arguments = arguments;
        return this;
    }
}
