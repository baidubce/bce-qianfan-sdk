package com.baidubce.qianfan.model.chat.V2;

import com.baidubce.qianfan.model.BaseResponse;
import com.baidubce.qianfan.model.chat.ChatUsage;

import java.util.List;

public class ChatV2Response extends BaseResponse<ChatV2Response> {
    private String model;

    private List<ChatChoice> choices;

    private ChatUsage usage;

    public String getModel() {
        return model;
    }

    public void setModel(String model) {
        this.model = model;
    }

    public List<ChatChoice> getChoices() {
        return choices;
    }

    public void setChoices(List<ChatChoice> choices) {
        this.choices = choices;
    }

    public ChatUsage getUsage() {
        return usage;
    }

    public void setUsage(ChatUsage usage) {
        this.usage = usage;
    }
}
