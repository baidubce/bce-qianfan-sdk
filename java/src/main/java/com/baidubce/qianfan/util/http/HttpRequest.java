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

import com.baidubce.qianfan.util.Json;
import com.baidubce.qianfan.util.TypeRef;
import org.apache.hc.client5.http.classic.methods.HttpUriRequestBase;
import org.apache.hc.core5.http.ClassicHttpRequest;
import org.apache.hc.core5.http.ContentType;
import org.apache.hc.core5.http.HttpEntity;
import org.apache.hc.core5.http.io.entity.ByteArrayEntity;
import org.apache.hc.core5.http.io.entity.StringEntity;

import java.io.IOException;
import java.lang.reflect.Type;
import java.net.URI;
import java.util.Iterator;
import java.util.LinkedHashMap;
import java.util.Map;

public class HttpRequest {
    private String url;
    private String method;
    private HttpEntity body;
    private Map<String, String> headers = new LinkedHashMap<>();

    public String getUrl() {
        return url;
    }

    public String getMethod() {
        return method;
    }

    public HttpEntity getBody() {
        return body;
    }

    public Map<String, String> getHeaders() {
        return headers;
    }

    public HttpRequest url(String url) {
        this.url = url;
        return this;
    }

    public HttpRequest method(String method) {
        this.method = method;
        return this;
    }

    public HttpRequest headers(Map<String, String> headers) {
        this.headers = headers;
        return this;
    }

    public HttpRequest get(String url) {
        this.method = "GET";
        this.url = url;
        return this;
    }

    public HttpRequest post(String url) {
        this.method = "POST";
        this.url = url;
        return this;
    }

    public HttpRequest put(String url) {
        this.method = "PUT";
        this.url = url;
        return this;
    }

    public HttpRequest delete(String url) {
        this.method = "DELETE";
        this.url = url;
        return this;
    }

    public <T> HttpRequest body(T body) {
        this.body = new StringEntity(Json.serialize(body), ContentType.APPLICATION_JSON);
        return this;
    }

    public HttpRequest body(byte[] body) {
        this.body = new ByteArrayEntity(body, ContentType.DEFAULT_BINARY);
        return this;
    }

    public HttpRequest addHeader(String key, String value) {
        this.headers.put(key, value);
        return this;
    }

    public <T> HttpResponse<T> executeJson(TypeRef<T> typeRef) throws IOException {
        return HttpClient.executeJson(toClassicHttpRequest(), typeRef);
    }

    public <T> HttpResponse<T> executeJson(Type type) throws IOException {
        return HttpClient.executeJson(toClassicHttpRequest(), type);
    }

    public HttpResponse<String> executeString() throws IOException {
        return HttpClient.executeString(toClassicHttpRequest());
    }

    public HttpResponse<Iterator<String>> executeSSE() throws IOException {
        return HttpClient.executeSSE(toClassicHttpRequest());
    }

    public HttpResponse<byte[]> execute() throws IOException {
        return HttpClient.execute(toClassicHttpRequest());
    }

    private ClassicHttpRequest toClassicHttpRequest() {
        ClassicHttpRequest request = new HttpUriRequestBase(this.method, URI.create(this.url));
        for (Map.Entry<String, String> entry : this.headers.entrySet()) {
            request.setHeader(entry.getKey(), entry.getValue());
        }
        if (this.body != null) {
            request.setEntity(body);
        }
        return request;
    }
}
