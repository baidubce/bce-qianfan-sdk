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

package com.baidubce.qianfan.model.rerank;

import com.baidubce.qianfan.model.BaseResponse;

import java.util.List;

public class RerankResponse extends BaseResponse<RerankResponse> {
    /**
     * 重排序结果，按相似性得分倒序
     */
    private List<RerankData> results;

    /**
     * token统计信息，token数 = 汉字数+单词数*1.3 （仅为估算逻辑）
     */
    private RerankUsage usage;

    public List<RerankData> getResults() {
        return results;
    }

    public RerankResponse setResults(List<RerankData> results) {
        this.results = results;
        return this;
    }

    public RerankUsage getUsage() {
        return usage;
    }

    public RerankResponse setUsage(RerankUsage usage) {
        this.usage = usage;
        return this;
    }
}
