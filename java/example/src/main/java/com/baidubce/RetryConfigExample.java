package com.baidubce;

import com.baidubce.qianfan.Qianfan;
import com.baidubce.qianfan.model.RetryConfig;
import com.baidubce.qianfan.model.chat.ChatResponse;

import java.util.Arrays;
import java.util.HashSet;

/**
 * 本示例实现了SDK配置重试策略
 */
public class RetryConfigExample {
    public static void main(String[] args) {
        setMaxRetryCount();
        setRetryWithErrCodes();
        setRetryWithBackoff();
    }

    private static void setMaxRetryCount() {
        RetryConfig retryConfig = new RetryConfig()
                .setRetryCount(3);

        Qianfan qianfan = new Qianfan()
                .setRetryConfig(retryConfig);

        ChatResponse response = qianfan.chatCompletion()
                .addMessage("user", "你好！你叫什么名字？")
                .execute();
        System.out.println(response.getResult());
    }

    private static void setRetryWithErrCodes() {
        RetryConfig retryConfig = new RetryConfig()
                .setRetryCount(3)
                .setRetryErrCodes(new HashSet<>(Arrays.asList(18, 336100)));

        Qianfan qianfan = new Qianfan()
                .setRetryConfig(retryConfig);

        ChatResponse response = qianfan.chatCompletion()
                .addMessage("user", "你好！你叫什么名字？")
                .execute();
        System.out.println(response.getResult());
    }

    private static void setRetryWithBackoff() {
        RetryConfig retryConfig = new RetryConfig()
                .setRetryCount(3)
                .setBackoffFactor(2)
                .setMaxWaitInterval(120);

        Qianfan qianfan = new Qianfan()
                .setRetryConfig(retryConfig);

        ChatResponse response = qianfan.chatCompletion()
                .addMessage("user", "你好！你叫什么名字？")
                .execute();
        System.out.println(response.getResult());
    }
}
