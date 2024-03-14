package com.baidubce;

import com.baidubce.qianfan.Qianfan;
import com.baidubce.qianfan.model.chat.ChatResponse;

/**
 * 本示例实现了一些常见的Chat调用流程
 */
public class ChatExample {
    public static void main(String[] args) {
        chat();
        multiTurnChat();
        customInferenceParameters();
        customModel();
        customEndpoint();
    }

    private static void chat() {
        Qianfan qianfan = new Qianfan();
        ChatResponse response = qianfan.chatCompletion()
                .addMessage("user", "你好！你叫什么名字？")
                .execute();
        System.out.println(response.getResult());
    }

    private static void multiTurnChat() {
        Qianfan qianfan = new Qianfan();
        ChatResponse response = qianfan.chatCompletion()
                // 通过传入历史对话记录来实现多轮对话
                .addMessage("user", "你好！你叫什么名字？")
                .addMessage("assistant", "你好！我是文心一言，英文名是ERNIE Bot。")
                // 传入本轮对话的用户输入
                .addMessage("user", "刚刚我的问题是什么？")
                .execute();
        System.out.println(response.getResult());
    }

    private static void customInferenceParameters() {
        Qianfan qianfan = new Qianfan();
        ChatResponse response = qianfan.chatCompletion()
                // 设置温度
                .temperature(0.5)
                // 设置top_p
                .topP(0.9)
                .addMessage("user", "你好！你叫什么名字？")
                .execute();
        System.out.println(response.getResult());
    }

    private static void customModel() {
        Qianfan qianfan = new Qianfan();
        ChatResponse response = qianfan.chatCompletion()
                // 设置需要使用的模型，与endpoint同时只能设置一种
                .model("ERNIE-Bot")
                .addMessage("user", "你好！你叫什么名字？")
                .execute();
        System.out.println(response.getResult());
    }

    private static void customEndpoint() {
        Qianfan qianfan = new Qianfan();
        ChatResponse response = qianfan.chatCompletion()
                // 设置需要使用的模型endpoint，用户自行训练的模型应当使用endpoint调用
                .endpoint("eb-instant")
                .addMessage("user", "你好！你叫什么名字？")
                .execute();
        System.out.println(response.getResult());
    }
}
