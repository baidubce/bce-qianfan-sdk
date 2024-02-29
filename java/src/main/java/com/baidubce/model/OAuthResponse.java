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

package com.baidubce.model;

public class OAuthResponse {
    private String refreshToken;

    private String expiresIn;

    private String sessionKey;

    private String accessToken;

    private String scope;

    private String sessionSecret;

    public String getRefreshToken() {
        return refreshToken;
    }

    public OAuthResponse setRefreshToken(String refreshToken) {
        this.refreshToken = refreshToken;
        return this;
    }

    public String getExpiresIn() {
        return expiresIn;
    }

    public OAuthResponse setExpiresIn(String expiresIn) {
        this.expiresIn = expiresIn;
        return this;
    }

    public String getSessionKey() {
        return sessionKey;
    }

    public OAuthResponse setSessionKey(String sessionKey) {
        this.sessionKey = sessionKey;
        return this;
    }

    public String getAccessToken() {
        return accessToken;
    }

    public OAuthResponse setAccessToken(String accessToken) {
        this.accessToken = accessToken;
        return this;
    }

    public String getScope() {
        return scope;
    }

    public OAuthResponse setScope(String scope) {
        this.scope = scope;
        return this;
    }

    public String getSessionSecret() {
        return sessionSecret;
    }

    public OAuthResponse setSessionSecret(String sessionSecret) {
        this.sessionSecret = sessionSecret;
        return this;
    }
}