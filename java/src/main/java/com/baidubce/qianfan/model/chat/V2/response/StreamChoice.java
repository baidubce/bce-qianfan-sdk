package com.baidubce.qianfan.model.chat.V2.response;

public class StreamChoice extends BaseChoice<StreamChoice> {
    private Delta delta;

    public Delta getDelta() {
        return delta;
    }

    public StreamChoice setDelta(Delta delta) {
        this.delta = delta;
        return this;
    }
}
