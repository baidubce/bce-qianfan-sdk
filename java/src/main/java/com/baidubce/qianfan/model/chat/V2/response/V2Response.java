package com.baidubce.qianfan.model.chat.V2.response;

import java.util.List;

public class V2Response extends V2BaseResponse<V2Response> {
    private List<Choice> choices;

    public List<Choice> getChoices() {
        return this.choices;
    }

    public V2Response setChoices(List<Choice> choices) {
        this.choices = choices;
        return this;
    }
}
