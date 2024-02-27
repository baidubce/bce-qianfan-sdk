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

package com.baidubce.util.http;

import com.baidubce.util.Json;
import org.apache.hc.client5.http.impl.classic.CloseableHttpClient;
import org.apache.hc.client5.http.impl.classic.CloseableHttpResponse;
import org.apache.hc.client5.http.impl.classic.HttpClients;
import org.apache.hc.client5.http.impl.io.PoolingHttpClientConnectionManager;
import org.apache.hc.core5.http.ClassicHttpRequest;
import org.apache.hc.core5.http.Header;
import org.apache.hc.core5.http.HttpEntity;
import org.apache.hc.core5.http.HttpException;
import org.apache.hc.core5.http.io.entity.EntityUtils;

import java.io.IOException;
import java.util.Iterator;
import java.util.LinkedHashMap;
import java.util.Map;

public class HttpClient {
    private static final int MAX_CONNECTIONS = 128;

    private static final CloseableHttpClient client;

    static {
        PoolingHttpClientConnectionManager cm = new PoolingHttpClientConnectionManager();
        cm.setMaxTotal(MAX_CONNECTIONS);
        cm.setDefaultMaxPerRoute(MAX_CONNECTIONS);

        client = HttpClients.custom().setConnectionManager(cm).build();
    }

    private HttpClient() {
    }

    public static HttpRequest request() {
        return new HttpRequest();
    }

    public static <T> HttpResponse<T> executeJson(ClassicHttpRequest request, Class<T> clazz) throws IOException {
        return execute(request, (body, resp) -> resp.setBody(Json.deserialize(EntityUtils.toString(body), clazz)));
    }

    public static HttpResponse<String> executeString(ClassicHttpRequest request) throws IOException {
        return execute(request, (body, resp) -> resp.setBody(EntityUtils.toString(body)));
    }

    public static HttpResponse<byte[]> execute(ClassicHttpRequest request) throws IOException {
        return execute(request, (body, resp) -> resp.setBody(EntityUtils.toByteArray(body)));
    }

    private static <T> HttpResponse<T> execute(ClassicHttpRequest request, HttpResponseBodyHandler<T> bodyHandler)
            throws IOException {
        return client.execute(request, resp -> {
            Map<String, String> headers = new LinkedHashMap<>();
            for (Header header : resp.getHeaders()) {
                headers.put(header.getName(), header.getValue());
            }
            HttpResponse<T> response = new HttpResponse<T>().setCode(resp.getCode()).setHeaders(headers);
            return bodyHandler.handle(resp.getEntity(), response);
        });
    }

    public static HttpResponse<Iterator<String>> executeSSE(ClassicHttpRequest request) throws IOException {
        // Use legacy API to avoid auto-closing the response
        CloseableHttpResponse resp = client.execute(request);

        Map<String, String> headers = new LinkedHashMap<>();
        for (Header header : resp.getHeaders()) {
            headers.put(header.getName(), header.getValue());
        }

        return new HttpResponse<Iterator<String>>()
                .setCode(resp.getCode())
                .setHeaders(headers)
                .setBody(SSEWrapper.wrap(resp.getEntity().getContent(), resp));
    }

    @FunctionalInterface
    private interface HttpResponseBodyHandler<T> {
        HttpResponse<T> handle(HttpEntity entity, HttpResponse<T> response) throws HttpException, IOException;
    }
}
