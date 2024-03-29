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
import org.apache.hc.client5.http.impl.classic.CloseableHttpClient;
import org.apache.hc.client5.http.impl.classic.CloseableHttpResponse;
import org.apache.hc.client5.http.impl.classic.HttpClients;
import org.apache.hc.client5.http.impl.io.PoolingHttpClientConnectionManager;
import org.apache.hc.core5.http.*;
import org.apache.hc.core5.http.io.entity.EntityUtils;

import java.io.IOException;
import java.lang.reflect.Type;
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

    public static <T> HttpResponse<T> executeJson(ClassicHttpRequest request, TypeRef<T> typeRef) throws IOException {
        return executeJson(request, typeRef.getType());
    }

    public static <T> HttpResponse<T> executeJson(ClassicHttpRequest request, Type type) throws IOException {
        return execute(request, (body, resp) -> {
            String stringBody = EntityUtils.toString(body);
            return resp
                    .setStringBody(stringBody)
                    .setBody(Json.deserialize(stringBody, type));
        });
    }

    public static HttpResponse<String> executeString(ClassicHttpRequest request) throws IOException {
        return execute(request, (body, resp) -> {
            String stringBody = EntityUtils.toString(body);
            return resp.setStringBody(stringBody)
                    .setBody(stringBody);
        });
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
            HttpResponse<T> response = new HttpResponse<T>()
                    .setCode(resp.getCode())
                    .setHeaders(headers);
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

        Iterator<String> body = null;
        String stringBody = null;

        String contentType = headers.getOrDefault(ContentType.HEADER, "");
        if (contentType.startsWith(ContentType.TEXT_EVENT_STREAM)) {
            body = SSEWrapper.wrap(resp.getEntity().getContent(), resp);
        } else {
            try {
                // If the response is not an SSE stream, read the whole body as a string
                stringBody = EntityUtils.toString(resp.getEntity());
            } catch (ParseException e) {
                throw new IOException(e);
            }
        }

        return new HttpResponse<Iterator<String>>()
                .setCode(resp.getCode())
                .setHeaders(headers)
                .setBody(body)
                .setStringBody(stringBody);
    }

    @FunctionalInterface
    private interface HttpResponseBodyHandler<T> {
        HttpResponse<T> handle(HttpEntity entity, HttpResponse<T> response) throws HttpException, IOException;
    }
}
