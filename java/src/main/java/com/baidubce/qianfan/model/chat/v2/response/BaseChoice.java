package com.baidubce.qianfan.model.chat.v2.response;

import com.google.gson.annotations.SerializedName;

public class BaseChoice<T extends BaseChoice<T>> {
    private Integer index;

    @SerializedName("finish_reason")
    private String finishReason;

    private Integer flag;

    @SerializedName("ban_round")
    private Integer banRound;

    public Integer getIndex() {
        return index;
    }

    public BaseChoice<T> setIndex(Integer index) {
        this.index = index;
        return this;
    }

    public String getFinishReason() {
        return finishReason;
    }

    public BaseChoice<T> setFinishReason(String finishReason) {
        this.finishReason = finishReason;
        return this;
    }

    public Integer getFlag() {
        return flag;
    }

    public BaseChoice<T> setFlag(Integer flag) {
        this.flag = flag;
        return this;
    }

    public Integer getBanRound() {
        return banRound;
    }

    public BaseChoice<T> setBanRound(Integer banRound) {
        this.banRound = banRound;
        return this;
    }
}
