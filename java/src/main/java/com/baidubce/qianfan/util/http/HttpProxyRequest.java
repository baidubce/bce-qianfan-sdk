package com.baidubce.qianfan.util.http;

import com.baidubce.qianfan.model.ProxyConfig;
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

public class HttpProxyRequest extends HttpRequest {
    private String url;
    private String method;
    private HttpEntity body;
    private Map<String, String> headers = new LinkedHashMap<>();
    private static String host;
    private static int port;

    public String getUrl() {
        return url;
    }

    public String getMethod() {
        return method;
    }

    public HttpEntity getBody() {
        return body;
    }

    public String getHost() {
        return host;
    }

    public int getPort() {
        return port;
    }

    public Map<String, String> getHeaders() {
        return headers;
    }

    public HttpProxyRequest proxy(ProxyConfig proxyConfig) {
        this.host = proxyConfig.getProxyHost();
        this.port =proxyConfig.getProxyPort();
        return this;
    }
    public HttpProxyRequest url(String url) {
        this.url = url;
        return this;
    }

    public HttpProxyRequest method(String method) {
        this.method = method;
        return this;
    }

    public HttpProxyRequest headers(Map<String, String> headers) {
        this.headers = headers;
        return this;
    }

    public HttpProxyRequest get(String url) {
        this.method = "GET";
        this.url = url;
        return this;
    }

    public HttpProxyRequest post(String url) {
        this.method = "POST";
        this.url = url;
        return this;
    }

    public HttpProxyRequest put(String url) {
        this.method = "PUT";
        this.url = url;
        return this;
    }

    public HttpProxyRequest delete(String url) {
        this.method = "DELETE";
        this.url = url;
        return this;
    }

    public <T> HttpRequest body(T body) {
        this.body = new StringEntity(Json.serialize(body), org.apache.hc.core5.http.ContentType.APPLICATION_JSON);
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
        return  new HttpProxyClient(host,port).build().executeJson(toClassicHttpRequest(), type);
    }

    public HttpResponse<String> executeString() throws IOException {
        return new HttpProxyClient(host,port).build().executeString(toClassicHttpRequest());
    }

    public HttpResponse<Iterator<String>> executeSSE() throws IOException {
        return new HttpProxyClient(host,port).build().executeSSE(toClassicHttpRequest());
    }

    public HttpResponse<byte[]> execute() throws IOException {
        return new HttpProxyClient(host,port).build().execute(toClassicHttpRequest());
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
