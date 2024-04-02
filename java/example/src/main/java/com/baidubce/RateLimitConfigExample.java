package com.baidubce;

import com.baidubce.qianfan.Qianfan;
import com.baidubce.qianfan.model.RateLimitConfig;
import com.baidubce.qianfan.model.chat.ChatResponse;

/**
 * 本示例实现了SDk的QPS和RPM的限流功能，两种限流方式不可同时设置
 */
public class RateLimitConfigExample {
    public static void main(String[] args) {
        setQPSLimit();
        setRPMLimit();
    }

    public static void setQPSLimit() {
        RateLimitConfig rateLimitConfig = new RateLimitConfig()
                .setQpsLimit(3);

        Qianfan qianfan = new Qianfan()
                .setRateLimitConfig(rateLimitConfig);

        ChatResponse response = qianfan.chatCompletion()
                .addMessage("user", "你好！你叫什么名字？")
                .execute();
        System.out.println(response.getResult());
    }

    public static void setRPMLimit() {
        RateLimitConfig rateLimitConfig = new RateLimitConfig()
                .setRpmLimit(3);

        Qianfan qianfan = new Qianfan()
                .setRateLimitConfig(rateLimitConfig);

        ChatResponse response = qianfan.chatCompletion()
                .addMessage("user", "你好！你叫什么名字？")
                .execute();
        System.out.println(response.getResult());
    }
}
