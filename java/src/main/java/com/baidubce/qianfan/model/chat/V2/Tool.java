package com.baidubce.qianfan.model.chat.V2;

public class Tool {
    private String name;

    private String description;

    private Object parameters;

    public static final String type = "function";

    public String getName() {
        return name;
    }

    public void setName(String name) {
        this.name = name;
    }

    public String getDescription() {
        return description;
    }

    public void setDescription(String description) {
        this.description = description;
    }

    public Object getParameters() {
        return parameters;
    }

    public void setParameters(Object parameters) {
        this.parameters = parameters;
    }
}
