package com.baidubce.qianfan.model.chat.V2.response;

import com.baidubce.qianfan.model.BaseResponse;
import com.baidubce.qianfan.model.chat.ChatUsage;

public abstract class V2BaseResponse<T extends V2BaseResponse<T>> extends BaseResponse<T> {
    private String model;

    private ChatUsage usage;

    public String getModel() {
        return model;
    }

    public V2BaseResponse<T> setModel(String model) {
        this.model = model;
        return this;
    }

    public ChatUsage getUsage() {
        return usage;
    }

    public V2BaseResponse<T> setUsage(ChatUsage usage) {
        this.usage = usage;
        return this;
    }
}
