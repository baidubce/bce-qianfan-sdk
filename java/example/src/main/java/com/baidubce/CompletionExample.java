package com.baidubce;

import com.baidubce.qianfan.Qianfan;
import com.baidubce.qianfan.model.completion.CompletionResponse;

/**
 * 本示例实现了最简单的Completion调用流程
 */
public class CompletionExample {
    public static void main(String[] args) {
        Qianfan qianfan = new Qianfan();
        CompletionResponse response = qianfan.completion()
                .prompt("hello")
                .execute();
        System.out.println(response.getResult());
    }
}
