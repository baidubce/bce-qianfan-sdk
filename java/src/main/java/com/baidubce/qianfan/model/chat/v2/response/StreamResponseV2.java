package com.baidubce.qianfan.model.chat.v2.response;

import java.util.List;

public class StreamResponseV2 extends BaseResponseV2<StreamResponseV2> {
    private List<StreamChoice> choices;

    public List<StreamChoice> getChoices() {
        return choices;
    }

    public StreamResponseV2 setChoices(List<StreamChoice> choices) {
        this.choices = choices;
        return this;
    }
}
