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

package com.baidubce.qianfan.util;

import java.util.concurrent.Executors;
import java.util.concurrent.ScheduledExecutorService;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.locks.Condition;
import java.util.concurrent.locks.Lock;
import java.util.concurrent.locks.ReentrantLock;

public class TokenBucketLimiter {
    private final Lock lock = new ReentrantLock();
    private final Condition condition = lock.newCondition();
    private final ScheduledExecutorService scheduler;
    private int maxTokens;
    private int availableTokens;

    public TokenBucketLimiter(int maxTokens, int refillPeriod) {
        if (maxTokens <= 0) {
            throw new IllegalArgumentException("maxTokens should be positive");
        }
        if (refillPeriod <= 0) {
            throw new IllegalArgumentException("refillPeriod should be positive");
        }
        this.maxTokens = maxTokens;
        this.availableTokens = maxTokens;
        this.scheduler = Executors.newSingleThreadScheduledExecutor(r -> {
            Thread t = new Thread(r);
            t.setDaemon(true);
            return t;
        });
        this.scheduler.scheduleAtFixedRate(this::refill, refillPeriod, refillPeriod, TimeUnit.SECONDS);
    }

    public void acquire() throws InterruptedException {
        acquire(1);
    }

    public void acquire(int tokens) throws InterruptedException {
        if (tokens <= 0) {
            throw new IllegalArgumentException("tokens should be positive");
        }
        if (tokens > maxTokens) {
            throw new IllegalArgumentException("tokens should be less than or equal to maxTokens");
        }
        lock.lock();
        try {
            while (tokens > availableTokens) {
                condition.await();
            }
            availableTokens -= tokens;
        } finally {
            lock.unlock();
        }
    }

    public void updateMaxTokens(int maxTokens, boolean resetAvailableTokens) {
        if (maxTokens <= 0) {
            throw new IllegalArgumentException("maxTokens should be positive");
        }
        lock.lock();
        try {
            this.maxTokens = maxTokens;
            if (resetAvailableTokens) {
                refill();
            }
        } finally {
            lock.unlock();
        }
    }

    private void refill() {
        lock.lock();
        try {
            availableTokens = maxTokens;
            condition.signalAll();
        } finally {
            lock.unlock();
        }
    }
}
