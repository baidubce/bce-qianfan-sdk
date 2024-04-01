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

package com.baidubce.qianfan.core;

import com.baidubce.qianfan.model.RateLimitConfig;
import com.baidubce.qianfan.model.RetryConfig;
import com.baidubce.qianfan.model.exception.ValidationException;
import com.baidubce.qianfan.util.EnvParser;

import java.io.FileNotFoundException;
import java.util.HashMap;
import java.util.HashSet;
import java.util.Map;
import java.util.Set;

public class QianfanConfig {
    private static final String QIANFAN_AK = "QIANFAN_AK";
    private static final String QIANFAN_SK = "QIANFAN_SK";
    private static final String QIANFAN_ACCESS_KEY = "QIANFAN_ACCESS_KEY";
    private static final String QIANFAN_SECRET_KEY = "QIANFAN_SECRET_KEY";
    private static final String QIANFAN_IAM_SIGN_EXPIRATION_SEC = "QIANFAN_IAM_SIGN_EXPIRATION_SEC";
    private static final String QIANFAN_ACCESS_TOKEN_REFRESH_MIN_INTERVAL = "QIANFAN_ACCESS_TOKEN_REFRESH_MIN_INTERVAL";
    private static final String QIANFAN_BASE_URL = "QIANFAN_BASE_URL";
    private static final String QIANFAN_CONSOLE_API_BASE_URL = "QIANFAN_CONSOLE_API_BASE_URL";
    private static final String QIANFAN_LLM_API_RETRY_COUNT = "QIANFAN_LLM_API_RETRY_COUNT";
    private static final String QIANFAN_LLM_API_RETRY_MAX_WAIT_INTERVAL = "QIANFAN_LLM_API_RETRY_MAX_WAIT_INTERVAL";
    private static final String QIANFAN_LLM_API_RETRY_BACKOFF_FACTOR = "QIANFAN_LLM_API_RETRY_BACKOFF_FACTOR";
    private static final String QIANFAN_LLM_API_RETRY_ERR_CODES = "QIANFAN_LLM_API_RETRY_ERR_CODES";
    private static final String QIANFAN_QPS_LIMIT = "QIANFAN_QPS_LIMIT";
    private static final String QIANFAN_RPM_LIMIT = "QIANFAN_RPM_LIMIT";

    private static final int DEFAULT_IAM_SIGN_EXPIRATION_SEC = 1800;
    private static final int DEFAULT_ACCESS_TOKEN_REFRESH_MIN_INTERVAL = 5;
    private static final String DEFAULT_BASE_URL = "https://aip.baidubce.com";
    private static final String DEFAULT_CONSOLE_API_BASE_URL = "https://qianfan.baidubce.com";
    private static final String DEFAULT_LLM_API_RETRY_COUNT = "1";
    private static final String DEFAULT_LLM_API_RETRY_MAX_WAIT_INTERVAL = "120";
    private static final String DEFAULT_LLM_API_RETRY_BACKOFF_FACTOR = "0";
    private static final String DEFAULT_LLM_API_RETRY_ERR_CODES = "18,336100";
    private static final String DEFAULT_QPS_LIMIT = "0";
    private static final String DEFAULT_RPM_LIMIT = "0";

    private static final String QIANFAN_DOT_ENV_CONFIG_FILE = "QIANFAN_DOT_ENV_CONFIG_FILE";
    private static final String DEFAULT_DOT_ENV_CONFIG_FILE = ".env";
    private static final Map<String, String> defaultConfigMap = new HashMap<>();
    private static final Map<String, String> fileConfigMap = new HashMap<>();

    static {
        try {
            defaultConfigMap.put(QIANFAN_IAM_SIGN_EXPIRATION_SEC, String.valueOf(DEFAULT_IAM_SIGN_EXPIRATION_SEC));
            defaultConfigMap.put(QIANFAN_ACCESS_TOKEN_REFRESH_MIN_INTERVAL, String.valueOf(DEFAULT_ACCESS_TOKEN_REFRESH_MIN_INTERVAL));
            defaultConfigMap.put(QIANFAN_BASE_URL, DEFAULT_BASE_URL);
            defaultConfigMap.put(QIANFAN_CONSOLE_API_BASE_URL, DEFAULT_CONSOLE_API_BASE_URL);
            defaultConfigMap.put(QIANFAN_LLM_API_RETRY_COUNT, DEFAULT_LLM_API_RETRY_COUNT);
            defaultConfigMap.put(QIANFAN_LLM_API_RETRY_MAX_WAIT_INTERVAL, DEFAULT_LLM_API_RETRY_MAX_WAIT_INTERVAL);
            defaultConfigMap.put(QIANFAN_LLM_API_RETRY_BACKOFF_FACTOR, DEFAULT_LLM_API_RETRY_BACKOFF_FACTOR);
            defaultConfigMap.put(QIANFAN_LLM_API_RETRY_ERR_CODES, DEFAULT_LLM_API_RETRY_ERR_CODES);
            defaultConfigMap.put(QIANFAN_QPS_LIMIT, DEFAULT_QPS_LIMIT);
            defaultConfigMap.put(QIANFAN_RPM_LIMIT, DEFAULT_RPM_LIMIT);
            String envConfigFile = System.getenv().getOrDefault(QIANFAN_DOT_ENV_CONFIG_FILE, DEFAULT_DOT_ENV_CONFIG_FILE);
            fileConfigMap.putAll(EnvParser.loadEnv(envConfigFile));
        } catch (FileNotFoundException e) {
            // ignored
        } catch (Exception e) {
            throw new ValidationException("Failed to load config from env file", e);
        }
    }

    private QianfanConfig() {
    }

    public static String getQianfanAk() {
        return getString(QIANFAN_AK);
    }

    public static String getQianfanSk() {
        return getString(QIANFAN_SK);
    }

    public static String getQianfanAccessKey() {
        return getString(QIANFAN_ACCESS_KEY);
    }

    public static String getQianfanSecretKey() {
        return getString(QIANFAN_SECRET_KEY);
    }

    public static Integer getIamSignExpirationSec() {
        return getInt(QIANFAN_IAM_SIGN_EXPIRATION_SEC);
    }

    public static Integer getAccessTokenRefreshMinInterval() {
        return getInt(QIANFAN_ACCESS_TOKEN_REFRESH_MIN_INTERVAL);
    }

    public static String getBaseUrl() {
        return getString(QIANFAN_BASE_URL);
    }

    public static String getConsoleApiBaseUrl() {
        return getString(QIANFAN_CONSOLE_API_BASE_URL);
    }

    public static RetryConfig getRetryConfig() {
        String[] errCodes = getString(QIANFAN_LLM_API_RETRY_ERR_CODES).split(",");
        Set<Integer> errCodeSet = new HashSet<>();
        for (String errCode : errCodes) {
            errCodeSet.add(Integer.parseInt(errCode));
        }
        return new RetryConfig()
                .setRetryCount(getInt(QIANFAN_LLM_API_RETRY_COUNT))
                .setMaxWaitInterval(getInt(QIANFAN_LLM_API_RETRY_MAX_WAIT_INTERVAL))
                .setBackoffFactor(getDouble(QIANFAN_LLM_API_RETRY_BACKOFF_FACTOR))
                .setRetryErrCodes(errCodeSet);
    }

    public static RateLimitConfig getRateLimitConfig() {
        return new RateLimitConfig()
                .setQpsLimit(getInt(QIANFAN_QPS_LIMIT))
                .setRpmLimit(getInt(QIANFAN_RPM_LIMIT));
    }

    public static Integer getInt(String key) {
        return Integer.parseInt(getString(key));
    }

    public static Double getDouble(String key) {
        return Double.parseDouble(getString(key));
    }

    public static String getString(String key) {
        if (fileConfigMap.containsKey(key)) {
            return fileConfigMap.get(key);
        }
        if (System.getenv().containsKey(key)) {
            return System.getenv().get(key);
        }
        return defaultConfigMap.get(key);
    }
}
