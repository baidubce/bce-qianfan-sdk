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
import com.baidubce.qianfan.core.auth.Auth;
import com.baidubce.qianfan.core.auth.IAuth;
import com.baidubce.qianfan.model.ApiErrorResponse;
import com.baidubce.qianfan.model.BaseRequest;
import com.baidubce.qianfan.model.RetryConfig;
import com.baidubce.qianfan.model.exception.ApiException;
import com.baidubce.qianfan.model.exception.QianfanException;
import com.baidubce.qianfan.model.exception.RequestException;
import com.baidubce.qianfan.util.Json;
import com.baidubce.qianfan.util.StringUtils;
import com.baidubce.qianfan.util.function.ThrowingFunction;
import com.baidubce.qianfan.util.function.ThrowingSupplier;
import com.baidubce.qianfan.util.http.*;

import java.util.Iterator;

class QianfanClient {
    private static final String SDK_VERSION = "0.0.1";
    private static final String QIANFAN_URL_TEMPLATE = "%s/rpc/2.0/ai_custom/v1/wenxinworkshop%s";
    private static final String EXTRA_PARAM_REQUEST_SOURCE = "request_source";
    private static final String REQUEST_SOURCE_PREFIX = "qianfan_java_sdk_v";
    private static final String REQUEST_SOURCE = REQUEST_SOURCE_PREFIX + SDK_VERSION;

    private final IAuth auth;
    private final ModelEndpointRetriever endpointRetriever;
    private RetryConfig retryConfig;

    public QianfanClient() {
        this(Auth.create());
    }

    public QianfanClient(String accessKey, String secretKey) {
        this(Auth.create(accessKey, secretKey));
    }

    public QianfanClient(String type, String accessKey, String secretKey) {
        this(Auth.create(type, accessKey, secretKey));
    }

    private QianfanClient(IAuth auth) {
        this.auth = auth;
        this.endpointRetriever = new ModelEndpointRetriever(auth);
        this.retryConfig = QianfanConfig.getRetryConfig();
    }

    public void setRetryConfig(RetryConfig retryConfig) {
        this.retryConfig = retryConfig;
    }

    @SuppressWarnings("unchecked")
    public <T, U extends BaseRequest<U>> T request(BaseRequest<U> request, Class<T> responseClass) {
        return request(
                () -> createHttpRequest(request).executeJson(responseClass),
                resp -> (T) resp.getBody()
        );
    }

    public <T, U extends BaseRequest<U>> Iterator<T> requestStream(BaseRequest<U> request, Class<T> responseClass) {
        return request(
                () -> createHttpRequest(request).executeSSE(),
                resp -> new StreamIterator<>(resp.getBody(), responseClass)
        );
    }

    private <T extends BaseRequest<T>> HttpRequest createHttpRequest(BaseRequest<T> baseRequest) {
        String finalEndpoint = endpointRetriever.getEndpoint(baseRequest.getType(), baseRequest.getModel(), baseRequest.getEndpoint());
        String url = String.format(QIANFAN_URL_TEMPLATE, QianfanConfig.getBaseUrl(), finalEndpoint);
        baseRequest.getExtraParameters().put(EXTRA_PARAM_REQUEST_SOURCE, REQUEST_SOURCE);
        HttpRequest request = HttpClient.request()
                .post(url)
                .body(baseRequest);
        return auth.signRequest(request);
    }

    private <T, R, E extends Exception> R request(ThrowingSupplier<HttpResponse<T>, E> respSupplier,
                                                  ThrowingFunction<HttpResponse<T>, R, E> respProcessor) {
        long startTime = System.currentTimeMillis();
        for (int i = 0; i < retryConfig.getRetryCount(); i++) {
            try {
                return innerRequest(respSupplier, respProcessor);
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
                backoffSleep(i, retryConfig.getBackoffFactor(), startTime, retryConfig.getMaxWaitInterval());
            }
        }
        throw new IllegalStateException("Request failed with unknown error");
    }

    private <T, R, E extends Exception> R innerRequest(ThrowingSupplier<HttpResponse<T>, E> respSupplier,
                                                       ThrowingFunction<HttpResponse<T>, R, E> respProcessor) {
        try {
            HttpResponse<T> resp = respSupplier.get();
            if (resp.getCode() != HttpStatus.SUCCESS) {
                throw new RequestException(String.format("Request failed with status code %d: %s", resp.getCode(), resp.getStringBody()));
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

    private void backoffSleep(int retryCount, double backoffFactor, long startTime, int totalRetryTimeout) throws RequestException {
        try {
            long baseDelay = (long) (Math.pow(2, retryCount) * backoffFactor * 1000);
            long elapsedTime = System.currentTimeMillis() - startTime;
            long adjustedDelay = Math.min(baseDelay, (long) totalRetryTimeout * 1000 - elapsedTime);
            Thread.sleep(adjustedDelay);
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
            throw new RequestException("Request failed: retry delay interrupted", e);
        }
    }

    private static class StreamIterator<T> implements Iterator<T> {
        private final Iterator<String> sseIterator;
        private final Class<T> responseClass;

        public StreamIterator(Iterator<String> sseIterator, Class<T> responseClass) {
            this.sseIterator = sseIterator;
            this.responseClass = responseClass;
        }

        @Override
        public boolean hasNext() {
            return sseIterator.hasNext();
        }

        @Override
        public T next() {
            String event = sseIterator.next().replaceFirst("data: ", "");
            // Skip sse empty line
            sseIterator.next();
            return Json.deserialize(event, responseClass);
        }
    }
}
