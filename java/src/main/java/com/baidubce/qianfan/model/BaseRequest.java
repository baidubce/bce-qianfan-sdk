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

package com.baidubce.qianfan.model;

import java.util.HashMap;
import java.util.Map;

public abstract class BaseRequest<T extends BaseRequest<T>> {
    /**
     * 模型名称 (与endpoint二选一)
     */
    private String model;

    /**
     * 模型的调用端点 (与model二选一)
     */
    private String endpoint;

    /**
     * 表示最终用户的唯一标识符
     */
    private String userId;

    /**
     * 请求的额外参数
     */
    private Map<String, Object> extraParameters = new HashMap<>();

    public abstract String getType();

    public String getModel() {
        return model;
    }

    @SuppressWarnings("unchecked")
    public T setModel(String model) {
        this.model = model;
        return (T) this;
    }

    public String getEndpoint() {
        return endpoint;
    }

    @SuppressWarnings("unchecked")
    public T setEndpoint(String endpoint) {
        this.endpoint = endpoint;
        return (T) this;
    }

    public String getUserId() {
        return userId;
    }

    @SuppressWarnings("unchecked")
    public T setUserId(String userId) {
        this.userId = userId;
        return (T) this;
    }

    public Map<String, Object> getExtraParameters() {
        return extraParameters;
    }

    @SuppressWarnings("unchecked")
    public T setExtraParameters(Map<String, Object> extraParameters) {
        this.extraParameters = extraParameters;
        return (T) this;
    }
}
