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
import com.baidubce.qianfan.model.exception.AuthException;
import com.baidubce.qianfan.util.Pair;
import com.baidubce.qianfan.util.StringUtils;
import com.baidubce.qianfan.util.http.HttpRequest;

import javax.crypto.Mac;
import javax.crypto.spec.SecretKeySpec;
import java.io.UnsupportedEncodingException;
import java.net.URI;
import java.net.URLEncoder;
import java.nio.charset.StandardCharsets;
import java.security.InvalidKeyException;
import java.security.NoSuchAlgorithmException;
import java.text.SimpleDateFormat;
import java.util.*;
import java.util.stream.Collectors;

public class IAMAuth implements IAuth {
    private static final String HMAC_SHA256 = "HmacSHA256";
    private static final List<String> HEADER_TO_SIGN = Arrays.asList("host", "x-bce-date");
    private static final String SESSION_KEY_TEMPLATE = "bce-auth-v1/%s/%s/%s";
    private static final String SIGNATURE_TEMPLATE = "%s\n%s\n%s\n%s";
    private static final String AUTHORIZATION_TEMPLATE = "%s/%s/%s";

    private final String accessKey;
    private final String secretKey;

    public IAMAuth(String accessKey, String secretKey) {
        this.accessKey = accessKey;
        this.secretKey = secretKey;
    }

    @Override
    public String authType() {
        return Auth.TYPE_IAM;
    }

    @Override
    public HttpRequest signRequest(HttpRequest request) {
        try {
            return request
                    .addHeader("Authorization", sign(request.getMethod(), request.getUrl()))
                    .addHeader("X-Bce-Date", getTimestamp());
        } catch (Exception e) {
            throw new AuthException("Failed to sign request", e);
        }
    }

    private String sign(String method, String url) {
        int expirationInSeconds = QianfanConfig.getIamSignExpirationSec();
        String rawSessionKey = String.format(SESSION_KEY_TEMPLATE, accessKey, getTimestamp(), expirationInSeconds);
        String sessionKey = hash(rawSessionKey, secretKey);

        URI uri = URI.create(url);
        String canonicalQueryString = queryStringCanonicalization(uri.getQuery());

        Map<String, String> headers = new HashMap<>();
        headers.put("host", uri.getHost());
        headers.put("x-bce-date", getTimestamp());
        Pair<String, String[]> rv = headersCanonicalization(headers);
        String canonicalHeaders = rv.first;
        String signedHeaders = String.join(";", rv.second);

        String rawSignature = String.format(SIGNATURE_TEMPLATE, method, uri.getPath(), canonicalQueryString, canonicalHeaders);
        String signature = hash(rawSignature, sessionKey);

        return String.format(AUTHORIZATION_TEMPLATE, rawSessionKey, signedHeaders, signature);
    }

    private String getTimestamp() {
        SimpleDateFormat dateFormat = new SimpleDateFormat("yyyy-MM-dd'T'HH:mm:ss'Z'", Locale.US);
        dateFormat.setTimeZone(TimeZone.getTimeZone("UTC"));
        return dateFormat.format(new Date());
    }

    private String queryStringCanonicalization(String queryString) {
        if (StringUtils.isEmpty(queryString)) {
            return "";
        }
        Map<String, Object> params = new HashMap<>();
        for (String param : queryString.split("&")) {
            String[] pair = param.split("=");
            params.put(pair[0], pair[1]);
        }

        return params.entrySet().stream()
                .sorted(Map.Entry.comparingByKey())
                .map(entry -> entry.getKey() + "=" + normalize(entry.getValue().toString(), true))
                .collect(Collectors.joining("&"));
    }

    private Pair<String, String[]> headersCanonicalization(Map<String, String> headers) {
        List<String> canonicalHeaders = new ArrayList<>();
        List<String> signedHeadersList = new ArrayList<>();

        headers.entrySet().stream()
                .filter(entry -> StringUtils.isNotEmpty(entry.getValue()))
                .forEach(entry -> {
                    String key = entry.getKey().toLowerCase();
                    String value = entry.getValue().trim();
                    if (HEADER_TO_SIGN.contains(key)) {
                        canonicalHeaders.add(normalize(key, false) + ":" + normalize(value, false));
                        signedHeadersList.add(key);
                    }
                });

        Collections.sort(canonicalHeaders);
        Collections.sort(signedHeadersList);
        return new Pair<>(String.join("\n", canonicalHeaders), signedHeadersList.toArray(new String[0]));
    }

    private String normalize(String string, boolean encodingSlash) {
        try {
            String result = URLEncoder.encode(string, StandardCharsets.UTF_8.name())
                    .replace("+", "%20")
                    .replace("%21", "!")
                    .replace("%27", "'")
                    .replace("%28", "(")
                    .replace("%29", ")")
                    .replace("%2A", "*");
            if (!encodingSlash) {
                result = result.replace("%2F", "/");
            }
            return result;
        } catch (UnsupportedEncodingException ignored) {
            return "";
        }
    }

    private String hash(String data, String key) {
        try {
            Mac sha256Hmac = Mac.getInstance(HMAC_SHA256);
            sha256Hmac.init(new SecretKeySpec(key.getBytes(StandardCharsets.UTF_8), HMAC_SHA256));
            byte[] hashedBytes = sha256Hmac.doFinal(data.getBytes(StandardCharsets.UTF_8));
            return StringUtils.bytesToHexString(hashedBytes);
        } catch (NoSuchAlgorithmException | InvalidKeyException ignored) {
            return "";
        }
    }
}
