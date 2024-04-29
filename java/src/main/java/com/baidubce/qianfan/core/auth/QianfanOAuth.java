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

package com.baidubce.qianfan.core.auth;

import com.baidubce.qianfan.core.QianfanConfig;
import com.baidubce.qianfan.model.OAuthErrorResponse;
import com.baidubce.qianfan.model.OAuthResponse;
import com.baidubce.qianfan.model.ProxyConfig;
import com.baidubce.qianfan.model.exception.AuthException;
import com.baidubce.qianfan.model.exception.QianfanException;
import com.baidubce.qianfan.model.exception.RequestException;
import com.baidubce.qianfan.util.Json;
import com.baidubce.qianfan.util.StringUtils;
import com.baidubce.qianfan.util.http.HttpClient;
import com.baidubce.qianfan.util.http.HttpProxyClient;
import com.baidubce.qianfan.util.http.HttpRequest;
import com.baidubce.qianfan.util.http.HttpResponse;

import java.net.URI;

public class QianfanOAuth implements IAuth {
    private static final String OAUTH_URL = "%s/oauth/2.0/token?grant_type=client_credentials&client_id=%s&client_secret=%s";
    private static final String ACCESS_TOKEN = "access_token";
    private static final long EXPIRE_OFFSET_SECONDS = 10;
    private final String apiKey;
    private final String secretKey;
    private String token;
    private ProxyConfig proxyConfig;
    private volatile long tokenExpireAt;

    public QianfanOAuth(String apiKey, String secretKey) {
        this.apiKey = apiKey;
        this.secretKey = secretKey;
    }

    public QianfanOAuth(String apiKey, String secretKey, ProxyConfig proxyConfig) {
        this.apiKey = apiKey;
        this.secretKey = secretKey;
        this.proxyConfig=proxyConfig;
    }

    @Override
    public HttpRequest signRequest(HttpRequest request) {
        String accessToken = getToken();
        String url = request.getUrl();
        if (URI.create(url).getQuery() == null) {
            url += "?" + ACCESS_TOKEN + "=" + accessToken;
        } else {
            url += "&" + ACCESS_TOKEN + "=" + accessToken;
        }
        return request.url(url);
    }

    private String getToken() {
        if (isTokenExpired()) {
            synchronized (this) {
                if (isTokenExpired()) {
                    token = sign();
                    long expiresIn = QianfanConfig.getAccessTokenRefreshMinInterval();
                    if (expiresIn > EXPIRE_OFFSET_SECONDS) {
                        // Subtract offset seconds to avoid token expiration during request
                        expiresIn -= EXPIRE_OFFSET_SECONDS;
                    }
                    tokenExpireAt = System.currentTimeMillis() / 1000 + expiresIn;
                }
            }
        }
        return token;
    }

    private boolean isTokenExpired() {
        return System.currentTimeMillis() / 1000 > tokenExpireAt;
    }

    private String sign() {
        String url = String.format(OAUTH_URL, QianfanConfig.getBaseUrl(), apiKey, secretKey);
        try {
            HttpResponse<OAuthResponse> resp;
            if ("".equals(proxyConfig.getProxyHost())||proxyConfig.getProxyPort()==0){
                resp = HttpClient.request().get(url).executeJson(OAuthResponse.class);
            }else{
                resp = new HttpProxyClient(proxyConfig.getProxyHost(),proxyConfig.getProxyPort()).build().request().get(url).executeJson(OAuthResponse.class);
            }
            if (resp.getCode() > 400 || StringUtils.isEmpty(resp.getBody().getAccessToken())) {
                OAuthErrorResponse errorResp = Json.deserialize(resp.getStringBody(), OAuthErrorResponse.class);
                throw new AuthException("Auth failed with error", errorResp);
            }
            return resp.getBody().getAccessToken();
        } catch (QianfanException e) {
            throw e;
        } catch (Exception e) {
            throw new RequestException(String.format("Auth request failed: %s", e.getMessage()), e);
        }
    }
}