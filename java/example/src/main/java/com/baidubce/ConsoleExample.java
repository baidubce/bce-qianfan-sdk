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
import com.baidubce.qianfan.util.CollUtils;

import java.util.Map;

/**
 * 本示例实现了Console管控API调用流程
 * API文档可见 <a href="https://cloud.baidu.com/doc/WENXINWORKSHOP/s/Ely8ai160">API列表</a>
 */
public class ConsoleExample {
    public static void main(String[] args) {
        describePresetServices();
        describeTPMResource();
    }

    private static void describePresetServices() {
        // 获取预置服务列表 https://cloud.baidu.com/doc/WENXINWORKSHOP/s/Glygmrg7v
        Map<String, Object> response = new Qianfan().console()
                // 对应文档中请求地址的后缀
                .route("/v2/service")
                // 对应文档中Query参数的Action
                .action("DescribePresetServices")
                // 如果不传入任何Response类，则默认返回Map<String, Object>
                .execute()
                // 可以传入class或者TypeRef来指定反序列化后返回的Response类
                // .execute(DescribePresetServicesResponse.class)
                .getResult();
        System.out.println(response);
    }

    private static void describeTPMResource() {
        // 查询TPM配额信息详情 https://cloud.baidu.com/doc/WENXINWORKSHOP/s/ultmls9l9
        Map<String, Object> response = new Qianfan().console().route("/v2/charge").action("DescribeTPMResource")
                // 需要传入参数的场景，可以自行封装请求类，或者使用Map.of()来构建请求Body
                // Java 8可以使用SDK提供的CollUtils.mapOf()来替代Map.of()
                .body(CollUtils.mapOf(
                        "model", "ernie-4.0-8k",
                        "paymentTiming", "Postpaid"
                ))
                .execute()
                .getResult();
        System.out.println(response);
    }
}


