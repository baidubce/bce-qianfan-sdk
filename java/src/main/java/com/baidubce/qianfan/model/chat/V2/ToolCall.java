package com.baidubce.qianfan.model.chat.V2;

public class ToolCall {

    private String id;

    private String name;

    private String arguments;

    public static final String type = "function";

    public String getId() {
        return id;
    }

    public void setId(String id) {
        this.id = id;
    }

    public String getName() {
        return name;
    }

    public void setName(String name) {
        this.name = name;
    }

    public String getArguments() {
        return arguments;
    }

    public void setArguments(String arguments) {
        this.arguments = arguments;
    }
}
