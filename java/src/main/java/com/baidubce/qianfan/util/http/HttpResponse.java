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

package com.baidubce.qianfan.util.http;

import java.util.Map;

public class HttpResponse<T> {
    private int code;
    private Map<String, String> headers;

    private T body;

    private String stringBody;

    public int getCode() {
        return code;
    }

    protected HttpResponse<T> setCode(int code) {
        this.code = code;
        return this;
    }

    public Map<String, String> getHeaders() {
        return headers;
    }

    protected HttpResponse<T> setHeaders(Map<String, String> headers) {
        this.headers = headers;
        return this;
    }

    public T getBody() {
        return body;
    }

    protected HttpResponse<T> setBody(T body) {
        this.body = body;
        return this;
    }

    public String getStringBody() {
        return stringBody;
    }

    protected HttpResponse<T> setStringBody(String stringBody) {
        this.stringBody = stringBody;
        return this;
    }
}
