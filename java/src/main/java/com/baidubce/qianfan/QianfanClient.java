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

package com.baidubce.qianfan;

import com.baidubce.qianfan.core.ModelEndpointRetriever;
import com.baidubce.qianfan.core.QianfanConfig;
import com.baidubce.qianfan.core.RateLimiter;
import com.baidubce.qianfan.core.StreamIterator;
import com.baidubce.qianfan.core.auth.Auth;
import com.baidubce.qianfan.core.auth.IAMAuth;
import com.baidubce.qianfan.core.auth.IAuth;
import com.baidubce.qianfan.model.*;
import com.baidubce.qianfan.model.chat.v2.request.RequestV2;
import com.baidubce.qianfan.model.console.ConsoleRequest;
import com.baidubce.qianfan.model.console.ConsoleResponse;
import com.baidubce.qianfan.model.embedding.v2.EmbeddingRequestV2;
import com.baidubce.qianfan.model.exception.ApiException;
import com.baidubce.qianfan.model.exception.AuthException;
import com.baidubce.qianfan.model.exception.QianfanException;
import com.baidubce.qianfan.model.exception.RequestException;
import com.baidubce.qianfan.model.rerank.v2.RerankRequestV2;
import com.baidubce.qianfan.util.Json;
import com.baidubce.qianfan.util.ParameterizedTypeImpl;
import com.baidubce.qianfan.util.StringUtils;
import com.baidubce.qianfan.util.function.ThrowingFunction;
import com.baidubce.qianfan.util.http.*;

import java.lang.reflect.Type;
import java.util.Map;

class QianfanClient {
    private static final String SDK_VERSION = "0.1.6";
    private static final String CONSOLE_URL_NO_ACTION_TEMPLATE = "%s%s";
    private static final String CONSOLE_URL_ACTION_TEMPLATE = "%s%s?Action=%s";
    private static final String QIANFAN_URL_TEMPLATE = "%s/rpc/2.0/ai_custom/v1/wenxinworkshop%s";
    private static final String QIANFAN_V2_CHAT_URL_TEMPLATE = "%s/v2/chat/completions";
    private static final String QIANFAN_V2_EMBEDDING_URL_TEMPLATE = "%s/v2/embeddings";
    private static final String QIANFAN_V2_RERANK_URL_TEMPLATE = "%s/v2/rerankers";
    private static final String EXTRA_PARAM_REQUEST_SOURCE = "request_source";
    private static final String REQUEST_SOURCE_PREFIX = "qianfan_java_sdk_v";
    private static final String REQUEST_SOURCE = REQUEST_SOURCE_PREFIX + SDK_VERSION;

    private IAuth auth;
    private ModelEndpointRetriever endpointRetriever;
    private RetryConfig retryConfig;
    private RateLimiter rateLimiter;

    public QianfanClient() {
        this(Auth.create());
    }

    public QianfanClient(String accessKey, String secretKey) {
        this(Auth.create(accessKey, secretKey));
    }

    public QianfanClient(String type, String accessKey, String secretKey) {
        this(Auth.create(type, accessKey, secretKey));
    }

    public QianfanClient(String bearerToken) {
        this(Auth.create(bearerToken));
    }

    private QianfanClient(IAuth auth) {
        this.auth = auth;
        this.endpointRetriever = new ModelEndpointRetriever(auth);
        this.retryConfig = QianfanConfig.getRetryConfig();
        this.rateLimiter = new RateLimiter(QianfanConfig.getRateLimitConfig());
    }

    public void setRetryConfig(RetryConfig retryConfig) {
        this.retryConfig = retryConfig;
    }

    public void setRateLimitConfig(RateLimitConfig rateLimitConfig) {
        this.rateLimiter = new RateLimiter(rateLimitConfig);
    }

    public QianfanClient covertToV2() {
        this.auth = auth.convertToV2();
        this.endpointRetriever = new ModelEndpointRetriever(auth);
        return this;
    }

    @SuppressWarnings("unchecked")
    public <T extends BaseResponse<T>, U extends BaseRequest<U>> T request(BaseRequest<U> request, Class<T> responseClass) {
        return request(
                request,
                req -> req.executeJson(responseClass),
                resp -> (T) ((T) resp.getBody()).setHeaders(resp.getHeaders()).setRawResponse(resp)
        );
    }

    public <T extends BaseResponse<T>, U extends BaseRequest<U>> StreamIterator<T> requestStream(BaseRequest<U> request, Class<T> responseClass) {
        return request(
                request,
                HttpRequest::executeSSE,
                resp -> new StreamIterator<>(resp.getHeaders(), resp.getBody(), responseClass)
        );
    }

    private <T extends BaseRequest<T>> HttpRequest createHttpRequest(BaseRequest<T> baseRequest) {
        String url;
        if (auth.authType().equals(Auth.TYPE_V2)) {
            String baseUrl = QianfanConfig.getConsoleApiBaseUrl();
            if (baseRequest instanceof RequestV2) {
                url = String.format(QIANFAN_V2_CHAT_URL_TEMPLATE, baseUrl);
            } else if (baseRequest instanceof EmbeddingRequestV2) {
                url = String.format(QIANFAN_V2_EMBEDDING_URL_TEMPLATE, baseUrl);
            } else if (baseRequest instanceof RerankRequestV2) {
                url = String.format(QIANFAN_V2_RERANK_URL_TEMPLATE, baseUrl);
            } else {
                throw new IllegalStateException("Construct request failed with unknown request type");
            }
        } else {
            String finalEndpoint = endpointRetriever.getEndpoint(baseRequest.getType(), baseRequest.getModel(), baseRequest.getEndpoint());
            url = String.format(QIANFAN_URL_TEMPLATE, QianfanConfig.getBaseUrl(), finalEndpoint);
        }
        baseRequest.getExtraParameters().put(EXTRA_PARAM_REQUEST_SOURCE, REQUEST_SOURCE);
        HttpRequest request = HttpClient.request()
                .post(url)
                .body(baseRequest);

        for (Map.Entry<String, String> entry : baseRequest.getHeaders().entrySet()) {
            request.addHeader(entry.getKey(), entry.getValue());
        }
        return auth.signRequest(request);
    }

    private <T extends BaseRequest<T>, U, V, E extends Exception> V request(
            BaseRequest<T> request,
            ThrowingFunction<HttpRequest, HttpResponse<U>, E> reqProcessor,
            ThrowingFunction<HttpResponse<U>, V, E> respProcessor) {
        for (int i = 0; i < retryConfig.getRetryCount(); i++) {
            try {
                return innerRequest(request, reqProcessor, respProcessor);
            } catch (RuntimeException ex) {
                if (ex instanceof ApiException) {
                    Integer errorCode = ((ApiException) ex).getErrorResponse().getErrorCode();
                    if (!retryConfig.getRetryErrCodes().contains(errorCode)) {
                        throw ex;
                    }
                }
                if (i == retryConfig.getRetryCount() - 1) {
                    throw ex;
                }
                backoffSleep(i, retryConfig.getBackoffFactor(), retryConfig.getMaxWaitInterval());
            }
        }
        throw new IllegalStateException("Request failed with unknown error");
    }

    public <T> ConsoleResponse<T> consoleRequest(ConsoleRequest request, Type type) {
        try {
            if (!(auth instanceof IAMAuth)) {
                throw new AuthException("Console request requires IAM authentication");
            }
            String url = StringUtils.isNotEmpty(request.getAction())
                    ? String.format(CONSOLE_URL_ACTION_TEMPLATE, QianfanConfig.getConsoleApiBaseUrl(), request.getRoute(), request.getAction())
                    : String.format(CONSOLE_URL_NO_ACTION_TEMPLATE, QianfanConfig.getConsoleApiBaseUrl(), request.getRoute());
            HttpRequest httpRequest = HttpClient.request()
                    .post(url)
                    .body(request.getBody() == null ? new Object() : request.getBody());

            Type respType = new ParameterizedTypeImpl(ConsoleResponse.class, new Type[]{type});
            HttpResponse<ConsoleResponse<T>> resp = auth.signRequest(httpRequest).executeJson(respType);

            if (resp.getCode() != HttpStatus.SUCCESS) {
                throw new RequestException(String.format("Request failed with status code %d: %s", resp.getCode(), resp.getStringBody()));
            }
            ApiErrorResponse errorResp = Json.deserialize(resp.getStringBody(), ApiErrorResponse.class);
            if (StringUtils.isNotEmpty(errorResp.getErrorMsg())) {
                throw new ApiException("Request failed with api error", errorResp);
            }
            return resp.getBody();
        } catch (QianfanException e) {
            throw e;
        } catch (Exception e) {
            throw new RequestException(String.format("Request failed: %s", e.getMessage()), e);
        }
    }

    private <T extends BaseRequest<T>, U, V, E extends Exception> V innerRequest(
            BaseRequest<T> request,
            ThrowingFunction<HttpRequest, HttpResponse<U>, E> reqProcessor,
            ThrowingFunction<HttpResponse<U>, V, E> respProcessor) {
        try {
            HttpRequest httpRequest = createHttpRequest(request);
            rateLimiter.acquire(httpRequest.getUrl());
            HttpResponse<U> resp = reqProcessor.apply(httpRequest);
            if (resp.getCode() != HttpStatus.SUCCESS) {
                throw new RequestException(String.format(
                        "Request failed with status code %d: %s\nheaders: %s",
                        resp.getCode(),
                        resp.getStringBody(),
                        resp.getHeaders().toString()
                ));
            }
            String contentType = resp.getHeaders().getOrDefault(ContentType.HEADER, "");
            if (contentType.startsWith(ContentType.APPLICATION_JSON)) {
                ApiErrorResponse errorResp = Json.deserialize(resp.getStringBody(), ApiErrorResponse.class);
                if (StringUtils.isNotEmpty(errorResp.getErrorMsg())) {
                    throw new ApiException("Request failed with api error", errorResp);
                }
            }
            return respProcessor.apply(resp);
        } catch (QianfanException e) {
            throw e;
        } catch (Exception e) {
            throw new RequestException(String.format("Request failed: %s", e.getMessage()), e);
        }
    }

    private void backoffSleep(int retryCount, double backoffFactor, int maxWaitInterval) throws RequestException {
        try {
            long delay = (long) (Math.pow(2, retryCount) * backoffFactor * 1000);
            Thread.sleep(Math.min(delay, maxWaitInterval * 1000L));
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
            throw new RequestException("Request failed: retry delay interrupted", e);
        }
    }
}
