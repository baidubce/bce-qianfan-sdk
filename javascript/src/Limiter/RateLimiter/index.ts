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

import Bottleneck from 'bottleneck';
import {Mutex} from 'async-mutex';
import {readEnvVariable} from '../../utils';

class RateLimiter {
    protected limiter: Bottleneck;
    protected qps?: number;
    protected rpm?: number;
    protected bufferRatio: number;
    private hasReset: boolean;
    private mutex: Mutex;

    constructor(queryPerSecond?: number, requestPerMinute?: number, bufferRatio: number = 0.1) {
        this.qps
            = this.safeParseInt(queryPerSecond) ?? Number(readEnvVariable('QIANFAN_QPS_LIMIT'));
        this.rpm
            = this.safeParseInt(requestPerMinute) ?? Number(readEnvVariable('QIANFAN_RPM_LIMIT'));
        this.bufferRatio = Math.min(Math.max(bufferRatio, 0), 1); // 保证bufferRatio在[0, 1]范围内
        this.mutex = new Mutex();
        this.hasReset = false;
        this.initializeLimiter();
    }

    private initializeLimiter(): void {
        // 如果两者都未设置，则不应用限流
        if (!this.qps && !this.rpm) {
            this.limiter = new Bottleneck({
                minTime: 0,
                highWater: -1,
                strategy: Bottleneck.strategy.OVERFLOW,
            });
            return;
        }
        let minTime = Number.MAX_SAFE_INTEGER;
        if (this.qps > 0) {
            minTime = Math.min(minTime, 1000 / this.qps);
        }
        if (this.rpm > 0) {
            // 取最小限制
            const rpmMinTime = Math.min(minTime, 60000 / this.rpm);
            minTime = Math.min(minTime, rpmMinTime);
        }
        // 确保 minTime 是一个合理的值
        minTime = Math.max(minTime, 0);
        this.limiter = new Bottleneck({
            minTime: minTime,
            highWater: -1,
            strategy: Bottleneck.strategy.OVERFLOW,
        });
    }

    /**
     * 使用限流器调度函数执行
     *
     * @param func 要调度的函数，返回一个Promise<T>
     * @returns 返回Promise<T>类型的调度结果
     */
    async schedule<T>(func: () => Promise<T>): Promise<T> {
        return this.limiter.schedule(func);
    }

    /**
     * 更新限制
     *
     * @param requestPerMinute 每分钟请求次数，可选参数
     */
    async updateLimits(requestPerMinute: number): Promise<void> {
        let release: () => void;
        try {
            // 使用hasReset检查是否已经进行过更新
            if (this.hasReset) {
                return;
            }
            release = await this.mutex.acquire();
            // 防止多个任务同时更新限制
            if (this.hasReset) {
                return;
            }
            if (requestPerMinute <= 0) {
                throw new Error('请求次数必须为正数');
            }
            if (this.rpm === requestPerMinute) {
                return;
            }
            this.rpm = this.safeParseInt(requestPerMinute, 'QIANFAN_RPM_LIMIT') ?? this.rpm;
            this.initializeLimiter();
            this.hasReset = true; // 确保只有第一个调用能够更新，并阻止后续调用
        }
        catch (error) {
            console.error('更新限制失败:', error);
        }
        finally {
            if (release) {
                release();
            }
        }
    }

    /**
     * 安全解析整数
     *
     * @param value 要解析的值，可以是数字或字符串
     * @param envVarName 环境变量名，用于输出警告信息
     * @returns 解析后的整数，若解析失败则返回 undefined
     */
    private safeParseInt(value?: number | string, envVarName?: string): number | undefined {
        if (!value) {
            return;
        }
        const parsedValue = Number.parseInt(String(value), 10);
        if (isNaN(parsedValue) || parsedValue < 0) {
            console.warn(`Invalid value for ${envVarName}: ${value}. Using undefined.`);
            return undefined;
        }
        return parsedValue;
    }
}

export default RateLimiter;
