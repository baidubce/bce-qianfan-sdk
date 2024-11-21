package com.baidubce.qianfan.model.chat.V2.response;

import java.util.List;

public class V2StreamResponse extends V2BaseResponse<V2StreamResponse> {
    private List<StreamChoice> choices;

    public List<StreamChoice> getChoices() {
        return choices;
    }

    public V2StreamResponse setChoices(List<StreamChoice> choices) {
        this.choices = choices;
        return this;
    }
}
