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

package com.baidubce.core.builder;

import com.baidubce.core.Qianfan;
import com.baidubce.model.exception.ValidationException;

import java.util.Map;

abstract class BaseBuilder<T extends BaseBuilder<T>> {
    private Qianfan qianfan;

    private String model;

    private String endpoint;

    private String userId;

    private ExtraParameterBuilder extraParameterBuilder = new ExtraParameterBuilder();

    protected BaseBuilder() {
    }

    protected BaseBuilder(Qianfan qianfan) {
        this.qianfan = qianfan;
    }

    @SuppressWarnings("unchecked")
    public T addExtraParameter(String key, Object value) {
        extraParameterBuilder.add(key, value);
        return (T) this;
    }

    @SuppressWarnings("unchecked")
    public T extraParameters(ExtraParameterBuilder extraParameters) {
        extraParameterBuilder = extraParameters;
        return (T) this;
    }

    @SuppressWarnings("unchecked")
    public T extraParameters(Map<String, Object> extraParameters) {
        extraParameterBuilder.extraParameters(extraParameters);
        return (T) this;
    }

    @SuppressWarnings("unchecked")
    public T model(String model) {
        this.model = model;
        return (T) this;
    }

    @SuppressWarnings("unchecked")
    public T endpoint(String endpoint) {
        this.endpoint = endpoint;
        return (T) this;
    }

    @SuppressWarnings("unchecked")
    public T userId(String userId) {
        this.userId = userId;
        return (T) this;
    }

    protected Qianfan getQianfan() {
        if (qianfan == null) {
            throw new ValidationException("Qianfan client is not set. " +
                    "please create builder from Qianfan client, " +
                    "or use build() instead of execute() to get Request and send it by yourself.");
        }
        return qianfan;
    }

    protected String getModel() {
        return model;
    }

    protected String getEndpoint() {
        return endpoint;
    }

    protected String getUserId() {
        return userId;
    }

    protected Map<String, Object> getExtraParameters() {
        return extraParameterBuilder.build();
    }
}
