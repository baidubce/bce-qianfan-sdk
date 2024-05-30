package com.baidubce;

import com.baidubce.qianfan.Qianfan;
import com.baidubce.qianfan.model.chat.ChatResponse;

/**
 * 本示例通过设置系统代理，实现了SDK的请求通过代理服务器发送
 */
public class HttpProxyExample {
    public static void main(String[] args) {
        System.setProperty("https.proxyHost", "127.0.0.1");
        System.setProperty("https.proxyPort", "7890");
        Qianfan qianfan = new Qianfan();
        ChatResponse response = qianfan.chatCompletion()
                .addMessage("user", "你好！我正在通过代理与你聊天哦")
                .execute();
        System.out.println(response.getResult());
    }
}
