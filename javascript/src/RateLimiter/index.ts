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
import {getDefaultConfig} from '../utils';

class RateLimiter {
    protected limiter: Bottleneck;
    protected qps?: number;
    protected rpm?: number;
    protected tpm?: number;
    protected bufferRatio: number;

    constructor(
        queryPerSecond?: number,
        requestPerMinute?: number,
        transactionPerMinute?: number,
        bufferRatio: number = 0.1
    ) {
        const defaultConfig = getDefaultConfig();
        this.qps = queryPerSecond ?? Number(defaultConfig.QIANFAN_QPS_LIMIT);
        this.rpm = requestPerMinute ?? Number(defaultConfig.QIANFAN_RPM_LIMIT);
        this.tpm = transactionPerMinute ?? Number(defaultConfig.QIANFAN_TPM_LIMIT);
        this.bufferRatio = bufferRatio;

        this.initializeLimiter();
    }

    private initializeLimiter(): void {
        let minTime = 0;

        if (this.qps) {
            minTime = Math.min(minTime || Infinity, 1000 / (this.qps * (1 - this.bufferRatio)));
        }
        if (this.rpm) {
            minTime = Math.min(minTime || Infinity, 60000 / (this.rpm * (1 - this.bufferRatio)));
        }
        if (this.tpm) {
            minTime = Math.min(minTime || Infinity, 60000 / (this.tpm * (1 - this.bufferRatio)));
        }

        this.limiter = new Bottleneck({
            minTime: minTime || 0,
        });
    }

    async schedule<T>(func: () => Promise<T>): Promise<T> {
        return this.limiter.schedule(func);
    }

    updateLimits(queryPerSecond?: number, requestPerMinute?: number, transactionPerMinute?: number): void {
        this.qps = queryPerSecond ?? this.qps;
        this.rpm = requestPerMinute ?? this.rpm;
        this.tpm = transactionPerMinute ?? this.tpm;

        this.initializeLimiter();
    }
}

export default RateLimiter;
