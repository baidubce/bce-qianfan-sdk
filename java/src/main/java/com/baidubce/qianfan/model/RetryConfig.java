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

package com.baidubce.qianfan.model;

import com.baidubce.qianfan.model.constant.APIErrorCode;

import java.util.Arrays;
import java.util.HashSet;
import java.util.Set;

public class RetryConfig {
    /**
     * retry count
     */
    private int retryCount = 1;

    /**
     * the max wait interval in seconds
     * Because exponential backoff retry policy is used, the actual wait
     * interval will be changed, this is to limit the max wait interval.
     */
    private int maxWaitInterval = 120;

    /**
     * backoff factor in exponential backoff retry policy
     */
    private double backoffFactor = 0;

    /**
     * API error codes used to catch for retrying
     */
    private Set<Integer> retryErrCodes = new HashSet<>(Arrays.asList(
            APIErrorCode.QPS_LIMIT_REACHED, APIErrorCode.SERVER_HIGH_LOAD
    ));

    public int getRetryCount() {
        return retryCount;
    }

    public RetryConfig setRetryCount(int retryCount) {
        this.retryCount = retryCount;
        return this;
    }

    public int getMaxWaitInterval() {
        return maxWaitInterval;
    }

    public RetryConfig setMaxWaitInterval(int maxWaitInterval) {
        this.maxWaitInterval = maxWaitInterval;
        return this;
    }

    public double getBackoffFactor() {
        return backoffFactor;
    }

    public RetryConfig setBackoffFactor(double backoffFactor) {
        this.backoffFactor = backoffFactor;
        return this;
    }

    public Set<Integer> getRetryErrCodes() {
        return retryErrCodes;
    }

    public RetryConfig setRetryErrCodes(Set<Integer> retryErrCodes) {
        this.retryErrCodes = retryErrCodes;
        return this;
    }
}
