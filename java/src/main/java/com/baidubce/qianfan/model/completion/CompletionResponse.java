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

package com.baidubce.qianfan.model.completion;

import com.baidubce.qianfan.model.BaseResponse;

public class CompletionResponse extends BaseResponse<CompletionResponse> {
    /**
     * 表示当前子句的序号。只有在流式接口模式下会返回该字段
     */
    private Integer sentenceId;

    /**
     * 表示当前子句是否是最后一句。只有在流式接口模式下会返回该字段
     */
    private Boolean isEnd;

    /**
     * 1：表示输入内容无安全风险 0：表示输入内容有安全风险
     */
    private Integer isSafe;

    /**
     * 对话返回结果
     */
    private String result;

    /**
     * token统计信息
     */
    private CompletionUsage usage;

    public Integer getSentenceId() {
        return sentenceId;
    }

    public CompletionResponse setSentenceId(Integer sentenceId) {
        this.sentenceId = sentenceId;
        return this;
    }

    public Boolean getEnd() {
        return isEnd;
    }

    public CompletionResponse setEnd(Boolean end) {
        isEnd = end;
        return this;
    }

    public Integer getIsSafe() {
        return isSafe;
    }

    public CompletionResponse setIsSafe(Integer isSafe) {
        this.isSafe = isSafe;
        return this;
    }

    public String getResult() {
        return result;
    }

    public CompletionResponse setResult(String result) {
        this.result = result;
        return this;
    }

    public CompletionUsage getUsage() {
        return usage;
    }

    public CompletionResponse setUsage(CompletionUsage usage) {
        this.usage = usage;
        return this;
    }
}
