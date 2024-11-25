package com.baidubce.qianfan.model.chat.v2.other;

import com.google.gson.annotations.SerializedName;

public class BearerTokenResponse {
    @SerializedName("userId")
    private String userId;

    private String token;

    private String status;

    @SerializedName("createTime")
    private String createTime;

    @SerializedName("expireTime")
    private String expireTime;

    public String getUserId() {
        return userId;
    }

    public void setUserId(String userId) {
        this.userId = userId;
    }

    public String getToken() {
        return token;
    }

    public void setToken(String token) {
        this.token = token;
    }

    public String getStatus() {
        return status;
    }

    public void setStatus(String status) {
        this.status = status;
    }

    public String getCreateTime() {
        return createTime;
    }

    public void setCreateTime(String createTime) {
        this.createTime = createTime;
    }

    public String getExpireTime() {
        return expireTime;
    }

    public void setExpireTime(String expireTime) {
        this.expireTime = expireTime;
    }
}
