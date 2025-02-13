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

import com.baidubce.qianfan.util.http.HttpResponse;

import java.util.Map;

public abstract class BaseResponse<T extends BaseResponse<T>> {
    /**
     * 请求的Id
     */
    private String id;

    /**
     * 回包类型。例如："image" 表示图像生成返回
     */
    private String object;

    /**
     * 时间戳
     */
    private Long created;

    /**
     * HTTP Response Headers
     */
    private Map<String, String> headers;

    private HttpResponse<Object> rawResponse;

    public String getId() {
        return id;
    }

    public BaseResponse<T> setId(String id) {
        this.id = id;
        return this;
    }

    public String getObject() {
        return object;
    }

    public BaseResponse<T> setObject(String object) {
        this.object = object;
        return this;
    }

    public Long getCreated() {
        return created;
    }

    public BaseResponse<T> setCreated(Long created) {
        this.created = created;
        return this;
    }

    public Map<String, String> getHeaders() {
        return headers;
    }

    public BaseResponse<T> setHeaders(Map<String, String> headers) {
        this.headers = headers;
        return this;
    }

    public HttpResponse<Object> getRawResponse() {
        return rawResponse;
    }

    public BaseResponse<T> setRawResponse(HttpResponse<Object> rawResponse) {
        this.rawResponse = rawResponse;
        return this;
    }
}
