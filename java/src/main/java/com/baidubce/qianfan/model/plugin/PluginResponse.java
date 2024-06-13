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

package com.baidubce.qianfan.model.plugin;

import com.baidubce.qianfan.model.BaseResponse;

public class PluginResponse extends BaseResponse<PluginResponse> {
    /**
     * 唯一的log id，用于问题定位
     */
    private Long logId;

    /**
     * 表示当前子句的序号，只有在流式接口模式下会返回该字段
     */
    private Integer sentenceId;

    /**
     * 表示当前子句是否是最后一句，只有在流式接口模式下会返回该字段
     */
    private Boolean isEnd;

    /**
     * 插件返回结果
     */
    private String result;

    /**
     * 当前生成的结果是否被截断
     */
    private Boolean isTruncated;

    /**
     * 表示用户输入是否存在安全，是否关闭当前会话，清理历史会话信息
     * true：是，表示用户输入存在安全风险，建议关闭当前会话，清理历史会话信息
     * false：否，表示用户输入无安全风险
     */
    private Boolean needClearHistory;

    /**
     * 当need_clear_history为true时，此字段会告知第几轮对话有敏感信息，如果是当前问题，ban_round = -1
     */
    private Integer banRound;

    /**
     * token统计信息，token数 = 汉字数+单词数*1.3 （仅为估算逻辑）
     */
    private PluginUsage usage;

    /**
     * 插件的原始请求信息
     */
    private PluginMetaInfo metaInfo;

    public Long getLogId() {
        return logId;
    }

    public PluginResponse setLogId(Long logId) {
        this.logId = logId;
        return this;
    }

    public Integer getSentenceId() {
        return sentenceId;
    }

    public PluginResponse setSentenceId(Integer sentenceId) {
        this.sentenceId = sentenceId;
        return this;
    }

    public Boolean getEnd() {
        return isEnd;
    }

    public PluginResponse setEnd(Boolean end) {
        isEnd = end;
        return this;
    }

    public String getResult() {
        return result;
    }

    public PluginResponse setResult(String result) {
        this.result = result;
        return this;
    }

    public Boolean getTruncated() {
        return isTruncated;
    }

    public PluginResponse setTruncated(Boolean truncated) {
        isTruncated = truncated;
        return this;
    }

    public Boolean getNeedClearHistory() {
        return needClearHistory;
    }

    public PluginResponse setNeedClearHistory(Boolean needClearHistory) {
        this.needClearHistory = needClearHistory;
        return this;
    }

    public Integer getBanRound() {
        return banRound;
    }

    public PluginResponse setBanRound(Integer banRound) {
        this.banRound = banRound;
        return this;
    }

    public PluginUsage getUsage() {
        return usage;
    }

    public PluginResponse setUsage(PluginUsage usage) {
        this.usage = usage;
        return this;
    }

    public PluginMetaInfo getMetaInfo() {
        return metaInfo;
    }

    public PluginResponse setMetaInfo(PluginMetaInfo metaInfo) {
        this.metaInfo = metaInfo;
        return this;
    }
}
