package com.baidubce.qianfan.model.chat.V2;

import com.google.gson.annotations.SerializedName;

public class ChatChoice {
    private Integer index;

    private Message message;

    @SerializedName("finish_reason")
    private String finishReason;

    private Integer flag;

    @SerializedName("ban_round")
    private Integer banRound;

    public Integer getIndex() {
        return index;
    }

    public void setIndex(Integer index) {
        this.index = index;
    }

    public Message getMessage() {
        return message;
    }

    public void setMessage(Message message) {
        this.message = message;
    }

    public String getFinishReason() {
        return finishReason;
    }

    public void setFinishReason(String finishReason) {
        this.finishReason = finishReason;
    }

    public Integer getFlag() {
        return flag;
    }

    public void setFlag(Integer flag) {
        this.flag = flag;
    }

    public Integer getBanRound() {
        return banRound;
    }

    public void setBanRound(Integer banRound) {
        this.banRound = banRound;
    }
}
