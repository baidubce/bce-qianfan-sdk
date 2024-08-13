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

package com.baidubce.qianfan.model.console;

public class ConsoleRequest {
    /**
     * 请求路由，例如/v2/service
     * route、action可参考文档: <a href="https://cloud.baidu.com/doc/WENXINWORKSHOP/s/Ely8ai160">API列表</a>
     */
    private String route;

    /**
     * 请求操作，例如DescribePresetServices
     */
    private String action;

    /**
     * 请求发送的POST数据
     */
    private Object body;

    public String getRoute() {
        return route;
    }

    public ConsoleRequest setRoute(String route) {
        this.route = route;
        return this;
    }

    public String getAction() {
        return action;
    }

    public ConsoleRequest setAction(String action) {
        this.action = action;
        return this;
    }

    public Object getBody() {
        return body;
    }

    public ConsoleRequest setBody(Object body) {
        this.body = body;
        return this;
    }
}
