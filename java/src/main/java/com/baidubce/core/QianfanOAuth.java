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

import com.baidubce.model.OAuthResponse;
import com.baidubce.model.exception.QianfanException;
import com.baidubce.util.http.HttpClient;
import com.baidubce.util.http.HttpResponse;

public class QianfanOAuth {
    private static final String AUTH_URL = "https://aip.baidubce.com/oauth/2.0/token?" +
            "grant_type=client_credentials&client_id=%s&client_secret=%s";
    private static final int DEFAULT_EXPIRE_SECONDS = 600;
    private static final int EXPIRE_OFFSET_SECONDS = 10;
    private final String apiKey;
    private final String secretKey;
    private String token;

    private volatile long tokenExpireAt;

    public QianfanOAuth(String apiKey, String secretKey) {
        this.apiKey = apiKey;
        this.secretKey = secretKey;
    }

    public String getToken() {
        if (isTokenExpired()) {
            synchronized (this) {
                if (isTokenExpired()) {
                    token = sign();
                    tokenExpireAt = System.currentTimeMillis() / 1000 + DEFAULT_EXPIRE_SECONDS - EXPIRE_OFFSET_SECONDS;
                }
            }
        }
        return token;
    }

    private boolean isTokenExpired() {
        return System.currentTimeMillis() / 1000 > tokenExpireAt;
    }

    private String sign() {
        String url = String.format(AUTH_URL, apiKey, secretKey);
        try {
            HttpResponse<OAuthResponse> resp = HttpClient.request().get(url).executeJson(OAuthResponse.class);
            if (resp.getCode() != 200) {
                throw new QianfanException("Failed to get token, response code: " + resp.getCode());
            }
            return resp.getBody().getAccessToken();
        } catch (Exception e) {
            throw new QianfanException("Failed to get token", e);
        }
    }
}
