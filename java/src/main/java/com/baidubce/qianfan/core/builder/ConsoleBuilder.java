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

package com.baidubce.qianfan.core.builder;

import com.baidubce.qianfan.Qianfan;
import com.baidubce.qianfan.model.console.ConsoleRequest;
import com.baidubce.qianfan.model.console.ConsoleResponse;
import com.baidubce.qianfan.model.exception.ValidationException;
import com.baidubce.qianfan.util.TypeRef;

import java.lang.reflect.Type;
import java.util.Map;

public class ConsoleBuilder {
    private Qianfan qianfan;

    private String route;

    private String action;

    private Object body;

    public ConsoleBuilder() {
        super();
    }

    public ConsoleBuilder(Qianfan qianfan) {
        this.qianfan = qianfan;
    }

    public ConsoleBuilder route(String route) {
        this.route = route;
        return this;
    }

    public ConsoleBuilder action(String action) {
        this.action = action;
        return this;
    }

    public ConsoleBuilder body(Object body) {
        this.body = body;
        return this;
    }

    public ConsoleRequest build() {
        return new ConsoleRequest()
                .setRoute(route)
                .setAction(action)
                .setBody(body);
    }

    public ConsoleResponse<Map<String, Object>> execute() {
        return executeWithCheck(new TypeRef<Map<String, Object>>() {}.getType());
    }

    public <T> ConsoleResponse<T> execute(TypeRef<T> typeRef) {
        return executeWithCheck(typeRef.getType());
    }

    public <T> ConsoleResponse<T> execute(Class<T> clazz) {
        return executeWithCheck(clazz);
    }

    public <T> ConsoleResponse<T> execute(Type type) {
        return executeWithCheck(type);
    }

    private <T> ConsoleResponse<T> executeWithCheck(Type type) {
        if (qianfan == null) {
            throw new ValidationException("Qianfan client is not set. " +
                    "please create builder from Qianfan client, " +
                    "or use build() instead of execute() to get Request and send it by yourself.");
        }
        return qianfan.consoleRequest(build(), type);
    }
}
