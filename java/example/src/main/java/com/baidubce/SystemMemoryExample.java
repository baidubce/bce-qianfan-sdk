/*
 * Copyright (c) 2024 Baidu, Inc. All Rights Reserved.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

package com.baidubce;

import com.baidubce.qianfan.Qianfan;
import com.baidubce.qianfan.core.auth.Auth;
import com.baidubce.qianfan.core.builder.MessageBuilder;
import com.baidubce.qianfan.model.chat.Message;
import com.baidubce.qianfan.util.CollUtils;

import java.util.List;
import java.util.Map;

/**
 * 本示例实现了简易的系统记忆管理接口及推理接口的全流程调用
 * 系统记忆Console接口文档可见 <a href="https://cloud.baidu.com/doc/WENXINWORKSHOP/s/Mlwg321zw">创建系统记忆</a>
 */
public class SystemMemoryExample {
    // 在模型服务-应用接入中创建应用，即可获得应用的AppID、API Key和Secret Key
    private static final String APP_ID = "替换为实际的AppId";
    private static final String APP_API_KEY = "替换为实际的ApiKey";
    private static final String APP_SECRET_KEY = "替换为实际的SecretKey";

    public static void main(String[] args) throws InterruptedException {
        // 注意，在生产环境中，应当手动创建一个系统记忆并维护记忆内容，然后在推理中重复使用该系统记忆
        String systemMemoryId = createSystemMemory(APP_ID, "度小茶饮品店智能客服系统记忆");
        System.out.println("系统记忆ID：" + systemMemoryId);

        Boolean result = modifySystemMemory(systemMemoryId, CollUtils.listOf(
                new MessageBuilder()
                        .add("user", "你的幸运数字是什么？")
                        .add("system", "我的幸运数字是42。")
                        .build(),
                new MessageBuilder()
                        .add("user", "能推荐一款适合夏天饮用的饮品吗？")
                        .add("system", "当然可以，我们推荐冰镇柠檬绿茶，清新爽口，非常适合夏日消暑。")
                        .build()
        ));
        System.out.println("修改系统记忆结果：" + result);

        Thread.sleep(5000);

        Map<String, Object> memories = describeSystemMemory(systemMemoryId);
        System.out.println("记忆列表：" + memories);

        String system = "你是度小茶饮品店的智能客服。";
        String response = chat(systemMemoryId, system, "你的幸运数字是什么");
        System.out.println("推理结果：" + response);
        String response2 = chat(systemMemoryId, system, "推荐一个适合夏天的饮料");
        System.out.println("推理结果2：" + response2);
    }

    private static String createSystemMemory(String appId, String description) {
        return new Qianfan().console()
                .route("/v2/memory")
                .action("CreateSystemMemory")
                .body(CollUtils.mapOf(
                        "appId", appId,
                        "description", description
                ))
                .execute(String.class)
                .getResult();
    }

    private static Boolean modifySystemMemory(String systemMemoryId, List<List<Message>> memories) {
        return new Qianfan().console()
                .route("/v2/memory")
                .action("ModifySystemMemory")
                .body(CollUtils.mapOf(
                        "systemMemoryId", systemMemoryId,
                        "memories", memories
                ))
                .execute(Boolean.class)
                .getResult();
    }

    private static Map<String, Object> describeSystemMemory(String systemMemoryId) {
        return new Qianfan().console()
                .route("/v2/memory")
                .action("DescribeSystemMemory")
                .body(CollUtils.mapOf(
                        "systemMemoryId", systemMemoryId
                ))
                .execute()
                .getResult();
    }

    private static String chat(String systemMemoryId, String system, String query) {
        // 使用系统记忆时，鉴权需要使用OAuth方式，同时需要传入与系统记忆相同应用的Api Key和Secret Key
        return new Qianfan(Auth.TYPE_OAUTH, APP_API_KEY, APP_SECRET_KEY).chatCompletion()
                .model("ERNIE-3.5-8K")
                .system(system)
                .enableSystemMemory(true)
                .systemMemoryId(systemMemoryId)
                .addUserMessage(query)
                .execute()
                .getResult();
    }
}
