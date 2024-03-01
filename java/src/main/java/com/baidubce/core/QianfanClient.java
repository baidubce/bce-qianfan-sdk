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

package com.baidubce.core;

import com.baidubce.core.auth.Auth;
import com.baidubce.core.auth.IAuth;
import com.baidubce.model.ApiErrorResponse;
import com.baidubce.model.BaseRequest;
import com.baidubce.model.constant.ModelEndpoint;
import com.baidubce.model.exception.ApiException;
import com.baidubce.model.exception.QianfanException;
import com.baidubce.model.exception.RequestException;
import com.baidubce.util.Json;
import com.baidubce.util.StringUtils;
import com.baidubce.util.http.HttpClient;
import com.baidubce.util.http.HttpRequest;
import com.baidubce.util.http.HttpResponse;

import java.util.HashMap;
import java.util.Iterator;

class QianfanClient {
    private static final String SDK_VERSION = "0.0.1";
    private static final String EXTRA_PARAM_REQUEST_SOURCE = "request_source";
    private static final String REQUEST_SOURCE_PREFIX = "qianfan_java_sdk_v";
    private static final String REQUEST_SOURCE = REQUEST_SOURCE_PREFIX + SDK_VERSION;

    private final IAuth auth;

    public QianfanClient() {
        this.auth = Auth.create();
    }

    public QianfanClient(String accessKey, String secretKey) {
        this.auth = Auth.create(accessKey, secretKey);
    }

    public QianfanClient(String type, String accessKey, String secretKey) {
        this.auth = Auth.create(type, accessKey, secretKey);
    }

    public <T, U extends BaseRequest<U>> T request(BaseRequest<U> request, Class<T> responseClass) {
        try {
            HttpResponse<T> resp = createHttpRequest(request).executeJson(responseClass);
            if (resp.getCode() != 200) {
                throw new ApiException(String.format("Request failed with status code %d: %s", resp.getCode(), resp.getStringBody()));
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

    public <T, U extends BaseRequest<U>> Iterator<T> requestStream(BaseRequest<U> request, Class<T> responseClass) {
        try {
            HttpResponse<Iterator<String>> resp = createHttpRequest(request).executeSSE();
            if (resp.getCode() != 200) {
                throw new ApiException(String.format("Request failed with status code %d: %s", resp.getCode(), resp.getStringBody()));
            }
            return new StreamIterator<>(resp.getBody(), responseClass);
        } catch (QianfanException e) {
            throw e;
        } catch (Exception e) {
            throw new RequestException(String.format("Request failed: %s", e.getMessage()), e);
        }
    }

    private <T extends BaseRequest<T>> HttpRequest createHttpRequest(BaseRequest<T> baseRequest) {
        if (baseRequest.getExtraParameters() == null) {
            baseRequest.setExtraParameters(new HashMap<>());
        }
        baseRequest.getExtraParameters().put(EXTRA_PARAM_REQUEST_SOURCE, REQUEST_SOURCE);
        HttpRequest request = HttpClient.request()
                .post(ModelEndpoint.getUrl(baseRequest.getEndpoint()))
                .body(baseRequest);
        return auth.signRequest(request);
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
