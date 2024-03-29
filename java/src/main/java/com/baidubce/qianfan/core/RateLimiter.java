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
import com.baidubce.qianfan.model.exception.RequestException;
import com.baidubce.qianfan.model.exception.ValidationException;
import com.baidubce.qianfan.util.TokenBucketLimiter;

import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

public class RateLimiter {
    private final int qpsLimit;
    private final int rpmLimit;
    private final Map<String, TokenBucketLimiter> limiterMap = new ConcurrentHashMap<>();

    public RateLimiter(RateLimitConfig config) {
        this.qpsLimit = config.getQpsLimit();
        this.rpmLimit = config.getRpmLimit();
        if (qpsLimit > 0 && rpmLimit > 0) {
            throw new ValidationException("Only one of qpsLimit and rpmLimit can be set");
        }
        if (qpsLimit < 0 || rpmLimit < 0) {
            throw new ValidationException("qpsLimit and rpmLimit must be non-negative");
        }
    }

    public void acquire(String key) {
        TokenBucketLimiter limiter = getLimiter(key);
        if (limiter != null) {
            try {
                limiter.acquire();
            } catch (InterruptedException e) {
                Thread.currentThread().interrupt();
                throw new RequestException("Rate limit acquire interrupted", e);
            }
        }
    }

    public void updateMaxTokens(String key, int maxTokens) {
        TokenBucketLimiter limiter = getLimiter(key);
        if (limiter != null) {
            limiter.updateMaxTokens(maxTokens, false);
        }
    }

    private TokenBucketLimiter getLimiter(String key) {
        return limiterMap.computeIfAbsent(key, k -> {
            if (qpsLimit > 0) {
                return new TokenBucketLimiter(qpsLimit, 1);
            }
            if (rpmLimit > 0) {
                return new TokenBucketLimiter(rpmLimit, 60);
            }
            return null;
        });
    }
}
