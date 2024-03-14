package com.baidubce;

import com.baidubce.qianfan.Qianfan;
import com.baidubce.qianfan.model.chat.Message;

import java.util.ArrayList;
import java.util.List;
import java.util.Scanner;

/**
 * 本示例实现了一个简易的命令行多轮对话工具
 */
public class CliStreamChatExample {
    public static void main(String[] args) {
        Qianfan qianfan = new Qianfan();
        // 保存对话记录
        List<Message> messages = new ArrayList<>();

        Scanner scanner = new Scanner(System.in);
        while (true) {
            System.out.print("输入: ");
            String input = scanner.nextLine();
            if ("exit".equals(input)) {
                break;
            }
            // 追加本轮用户输入
            messages.add(new Message().setRole("user").setContent(input));
            StringBuilder output = new StringBuilder();
            qianfan.chatCompletion()
                    .messages(messages)
                    // 使用流式执行
                    .executeStream()
                    .forEachRemaining(chunk -> {
                        // 打印输出并记录完整输出
                        System.out.print(chunk.getResult());
                        output.append(chunk.getResult());
                    });
            // 追加本轮助手输出
            messages.add(new Message().setRole("assistant").setContent(output.toString()));
            System.out.println();
        }
    }
}
