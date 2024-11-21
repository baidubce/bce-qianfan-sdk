package com.baidubce.qianfan.model.chat.V2.request;

import java.util.Map;

public class Function {
    private String name;

    private String description;

    private Map<String, Object> parameters;

    public String getName() {
        return name;
    }

    public Function setName(String name) {
        this.name = name;
        return this;
    }

    public String getDescription() {
        return description;
    }

    public Function setDescription(String description) {
        this.description = description;
        return this;
    }

    public Map<String, Object> getParameters() {
        return parameters;
    }

    public Function setParameters(Map<String, Object> parameters) {
        this.parameters = parameters;
        return this;
    }
}
