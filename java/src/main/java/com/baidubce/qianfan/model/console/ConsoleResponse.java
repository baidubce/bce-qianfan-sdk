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

import com.baidubce.qianfan.util.JsonProp;

public class ConsoleResponse<T> {
    /**
     * 请求ID
     */
    @JsonProp("logId")
    private String logId;

    /**
     * 请求结果
     */
    private T result;

    public String getLogId() {
        return logId;
    }

    public ConsoleResponse<T> setLogId(String logId) {
        this.logId = logId;
        return this;
    }

    public T getResult() {
        return result;
    }

    public ConsoleResponse<T> setResult(T result) {
        this.result = result;
        return this;
    }
}
