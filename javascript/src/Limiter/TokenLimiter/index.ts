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

import {Mutex} from 'async-mutex';
import {readEnvVariable} from '../../utils';

class TokenLimiter {
    private tokens: number;
    private maxTokens: number;
    private lastRefreshTime: Date;
    private mutex: Mutex;
    private bufferRatio: number;
    private initialMaxTokens: number;
    private hasReset: boolean;
    private readonly currentTime: () => Date = () => new Date();

    constructor(maxTokensPerMinute?: number, bufferRatio: number = 0.1) {
        this.bufferRatio = Math.min(Math.max(bufferRatio, 0), 1); // 保证bufferRatio在[0, 1]范围内
        // 使用局部变量缓存环境变量读取结果，避免多次读取
        const envMaxTokens = Number(readEnvVariable('QIANFAN_TPM_LIMIT')) || 0;
        this.initialMaxTokens = maxTokensPerMinute ?? envMaxTokens;
        // 如果未指定最大令牌数且环境变量也未定义，则不执行令牌限制
        if (!this.initialMaxTokens) {
            this.maxTokens = 0; // 设置为0表示无限制
        }
        else {
            // 使用缓冲区比率调整最大令牌数
            this.maxTokens = Math.floor(this.initialMaxTokens * (1 - this.bufferRatio));
        }
        this.tokens = this.maxTokens;
        this.lastRefreshTime = new Date();
        this.hasReset = false;
        this.mutex = new Mutex();
    }

    /**
     * 获取当前时间所在分钟的开始时间戳
     * @returns {number} 返回当前时间所在分钟的开始时间戳（毫秒）
     */
    private getTimeAtLastMinute(): number {
        return Math.floor(this.currentTime().getTime() / 60000) * 60000;
    }

    /**
     * 整分刷新令牌
     * @returns Promise<void>
     */
    private async refreshTokens(): Promise<void> {
        const nowAtMinute = this.getTimeAtLastMinute();
        if (nowAtMinute !== this.lastRefreshTime.getTime()) {
            this.tokens = this.maxTokens;
            this.lastRefreshTime = new Date(nowAtMinute);
        }
    }

    /**
     * 当前时间开始到下一分钟开始所需等待的时间（以毫秒为单位）
     * 如果在一个时间窗口（例如一分钟）内可用的令牌已经用完，需要等待直到下一个时间窗口开始才能再次填充令牌
     * @returns 等待时间
     */
    private timeUntilNextMinute(): number {
        const now = this.currentTime();
        const nextMinute = new Date(now);
        nextMinute.setMinutes(now.getMinutes() + 1);
        nextMinute.setSeconds(0);
        nextMinute.setMilliseconds(0);
        return nextMinute.getTime() - now.getTime();
    }

    /**
     * 当前是否有指定数量的可用令牌
     * 如果当前令牌数不足，它将计算等待时间直到下一分钟开始，并尝试再次刷新令牌。
     * @param tokenCount 令牌数量
     * @returns 返回Promise<boolean>类型，如果成功获取令牌，则返回true；否则返回false
     */
    public async acquireTokens(tokenCount: number): Promise<boolean> {
        if (this.maxTokens <= 0) {
            return true;
        }

        let release: () => void;
        try {
            release = await this.mutex.acquire();
            await this.refreshTokens();
            if (this.tokens >= tokenCount) {
                this.tokens -= tokenCount;
                return true;
            }
            await new Promise(resolve => setTimeout(resolve, this.timeUntilNextMinute()));
            return false;
        }
        catch (error) {
            console.error('Error acquiring tokens:', error);
            return false;
        }
        finally {
            if (release) {
                release();
            }
        }
    }

    /**
     * 重置令牌
     *
     * @param totalTokens 总的令牌数量
     */
    public async resetTokens(totalTokens: number): Promise<void> {
        let release: () => void;
        try {
            if (this.hasReset) {
                return;
            }
            release = await this.mutex.acquire();
            if (this.hasReset) {
                return;
            }
            // 检查如果传入的totalTokens与当前最大令牌数一致，则不做改变
            if (this.initialMaxTokens === totalTokens) {
                return;
            }
            // 之前设置过token
            if (this.maxTokens > 0) {
                totalTokens = Math.min(this.maxTokens, totalTokens);
            }
            const originalTokenCurrent = this.tokens;
            const originalTokenMax = this.maxTokens;
            const diff = originalTokenMax - originalTokenCurrent;
            // 重新设置最大令牌数，同时考虑缓冲区比率
            this.maxTokens = Math.floor(totalTokens * (1 - this.bufferRatio));
            this.tokens = Math.max(this.maxTokens - diff, 0);
            this.lastRefreshTime = new Date();
            this.hasReset = true;
        }
        catch (error) {
            console.error('Error resetting tokens:', error);
        }
        finally {
            if (release) {
                release();
            }
        }
    }

    /**
     * 计算文本中的 Token 数量
     *
     * @param text 要计算 Token 的文本
     * @returns 返回计算出的 Token 数量
     */
    public calculateTokens(text: string): number {
        const chineseCharactersCount = text.match(/[\u4e00-\u9fa5]/g)?.length || 0;
        const englishWordCount = text.match(/\b[a-zA-Z]+\b/g)?.length || 0;
        return chineseCharactersCount * 0.625 + englishWordCount;
    }

    public getTokens(): number {
        return this.tokens;
    }

    public getMaxTokens(): number {
        return this.maxTokens;
    }

    public setHasReset(value: boolean): void {
        this.hasReset = value;
    }
}

export default TokenLimiter;
