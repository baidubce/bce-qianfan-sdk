// Copyright (c) 2024 Baidu, Inc. All Rights Reserved.
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//     http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

import TokenLimiter from '../index';
import {Mutex} from 'async-mutex';

describe('TokenLimiter', () => {
    let tokenLimiter: TokenLimiter;
    let mutex: Mutex;
    jest.setTimeout(2000);
    beforeEach(() => {
        tokenLimiter = new TokenLimiter(1000, 0);
        mutex = new Mutex();
    });

    it('should handle multiple tasks concurrently', async () => {
        jest.setTimeout(2000); // 设置测试超时时间为2秒
        const tasks: Promise<boolean>[] = [];
        // 创建5个并发任务，每个任务减少100个令牌
        for (let i = 0; i < 5; i++) {
            tasks.push(tokenLimiter.acquireTokens(100));
        }
        // 等待所有任务完成
        await Promise.all(tasks);
        // 验证令牌消耗速度是否符合预期
        expect(tokenLimiter.getTokens()).toBe(500); // 期望剩余令牌数为500
    });

    it('acquires tokens if available', async () => {
        const acquireResult = await tokenLimiter.acquireTokens(500);
        expect(acquireResult).toBe(true);
        expect(tokenLimiter.getTokens()).toBe(500);
    });

    // 令牌限制器在获取令牌后的一分钟内自动刷新令牌的功能。
    it('refreshes tokens after one minute', async () => {
        jest.useFakeTimers();
        await tokenLimiter.acquireTokens(1000);
        jest.advanceTimersByTime(60000); // 快进一分钟
        const acquireResult = await tokenLimiter.acquireTokens(500);
        expect(acquireResult).toBe(true);
        expect(tokenLimiter.getTokens()).toBe(500);
    });

    it('should not reset tokens if hasReset is true', async () => {
        tokenLimiter.setHasReset(true);
        await tokenLimiter.resetTokens(500);
        expect(tokenLimiter.getTokens()).toBe(1000);
    });

    it('should unlock mutex if hasReset becomes true during locking', async () => {
        tokenLimiter.setHasReset(false);
        await mutex.acquire();
        tokenLimiter.setHasReset(true);
        await tokenLimiter.resetTokens(500);
        expect(tokenLimiter.getTokens()).toBe(1000);
    });

    it('should not change tokens if totalTokens is equal to originalTokenLimitPerMinute', async () => {
        tokenLimiter.setHasReset(false);
        const tasks: Promise<void>[] = [];
        // 创建5个并发任务，每个任务减少100个令牌
        for (let i = 0; i < 5; i++) {
            tasks.push(tokenLimiter.resetTokens(100));
        }
        // 等待所有任务完成
        await Promise.all(tasks);
        expect(tokenLimiter.getTokens()).toBe(100);
    });

    it('calculates token amount based on text', () => {
        const text = 'Hello, 世界!';
        const tokens = tokenLimiter.calculateTokens(text);
        expect(tokens).toBeGreaterThan(0); // 应根据实际计算方法确定期望值
    });
});
