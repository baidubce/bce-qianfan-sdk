package com.baidubce.qianfan.model.chat.v2.response;

import java.util.List;

public class ResponseV2 extends BaseResponseV2<ResponseV2> {
    private List<Choice> choices;

    public List<Choice> getChoices() {
        return this.choices;
    }

    public ResponseV2 setChoices(List<Choice> choices) {
        this.choices = choices;
        return this;
    }
}
