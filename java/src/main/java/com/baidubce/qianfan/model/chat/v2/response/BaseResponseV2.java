package com.baidubce.qianfan.model.chat.v2.response;

import com.baidubce.qianfan.model.BaseResponse;
import com.baidubce.qianfan.model.chat.ChatUsage;

public abstract class BaseResponseV2<T extends BaseResponseV2<T>> extends BaseResponse<T> {
    private String model;

    private ChatUsage usage;

    public String getModel() {
        return model;
    }

    public BaseResponseV2<T> setModel(String model) {
        this.model = model;
        return this;
    }

    public ChatUsage getUsage() {
        return usage;
    }

    public BaseResponseV2<T> setUsage(ChatUsage usage) {
        this.usage = usage;
        return this;
    }
}
