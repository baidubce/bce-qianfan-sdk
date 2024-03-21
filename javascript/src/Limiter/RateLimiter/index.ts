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
import {readEnvVariable} from '../../utils';

class RateLimiter {
    protected limiter: Bottleneck;
    protected qps?: number;
    protected rpm?: number;
    protected bufferRatio: number;

    constructor(queryPerSecond?: number, requestPerMinute?: number, bufferRatio: number = 0.1) {
        this.qps
            = this.safeParseInt(queryPerSecond) ?? Number(readEnvVariable('QIANFAN_QPS_LIMIT'));
        this.rpm
            = this.safeParseInt(requestPerMinute) ?? Number(readEnvVariable('QIANFAN_RPM_LIMIT'));
        this.bufferRatio = bufferRatio;

        this.initializeLimiter();
    }

    private initializeLimiter(): void {
        let minTime = Infinity; // 初始化为Infinity以确保能被后续计算正确更新

        if (this.qps) {
            minTime = Math.min(minTime, 1000 / (this.qps * (1 - this.bufferRatio)));
        }
        if (this.rpm) {
            minTime = Math.min(minTime, 60000 / (this.rpm * (1 - this.bufferRatio)));
        }

        this.limiter = new Bottleneck({
            minTime: minTime,
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
    updateLimits(requestPerMinute: number): void {
        this.rpm = this.safeParseInt(requestPerMinute, 'QIANFAN_RPM_LIMIT') ?? this.rpm;
        this.initializeLimiter();
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
        if (isNaN(parsedValue)) {
            console.warn(`Invalid value for ${envVarName}: ${value}. Using undefined.`);
            return undefined;
        }
        if (parsedValue < 0) {
            console.warn(`Negative value for ${envVarName}: ${value}. Using undefined.`);
            return undefined;
        }
        return parsedValue;
    }
}

export default RateLimiter;
