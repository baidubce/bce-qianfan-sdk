package com.baidubce.qianfan.model.chat.V2;

public class RequestToolChoice {
    private String mode;

    private String functionName;

    public static final String type = "function";

    public String getMode() {
        return mode;
    }

    public void setMode(String mode) {
        this.mode = mode;
    }

    public String getFunctionName() {
        return functionName;
    }

    public void setFunctionName(String functionName) {
        this.functionName = functionName;
    }
}
