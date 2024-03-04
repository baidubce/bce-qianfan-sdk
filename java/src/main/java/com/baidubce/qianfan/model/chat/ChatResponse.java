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

package com.baidubce.qianfan.model.chat;

public class ChatResponse {
    /**
     * 本轮对话的id
     */
    private String id;

    /**
     * 回包类型
     */
    private String object;

    /**
     * 时间戳
     */
    private Integer created;

    /**
     * 表示当前子句的序号。只有在流式接口模式下会返回该字段
     */
    private Integer sentenceId;

    /**
     * 表示当前子句是否是最后一句。只有在流式接口模式下会返回该字段
     */
    private Boolean isEnd;

    /**
     * 当前生成的结果是否被截断
     */
    private Boolean isTruncated;

    /**
     * 输出内容标识
     */
    private String finishReason;

    /**
     * 搜索数据，当请求参数enable_citation为true并且触发搜索时，会返回该字段
     */
    private SearchInfo searchInfo;

    /**
     * 对话返回结果
     */
    private String result;

    /**
     * 表示用户输入是否存在安全风险，是否关闭当前会话，清理历史会话信息
     */
    private Boolean needClearHistory;

    /**
     * 0：正常返回 其他：非正常
     */
    private Integer flag;

    /**
     * token统计信息
     */
    private ChatUsage usage;

    /**
     * 由模型生成的函数调用，包含函数名称，和调用参数
     */
    private FunctionCall functionCall;

    /**
     * 当need_clear_history为true时，此字段会告知第几轮对话有敏感信息，如果是当前问题，ban_round=-1
     */
    private Integer banRound;

    public String getId() {
        return id;
    }

    public ChatResponse setId(String id) {
        this.id = id;
        return this;
    }

    public String getObject() {
        return object;
    }

    public ChatResponse setObject(String object) {
        this.object = object;
        return this;
    }

    public Integer getCreated() {
        return created;
    }

    public ChatResponse setCreated(Integer created) {
        this.created = created;
        return this;
    }

    public Integer getSentenceId() {
        return sentenceId;
    }

    public ChatResponse setSentenceId(Integer sentenceId) {
        this.sentenceId = sentenceId;
        return this;
    }

    public Boolean getEnd() {
        return isEnd;
    }

    public ChatResponse setEnd(Boolean end) {
        isEnd = end;
        return this;
    }

    public Boolean getTruncated() {
        return isTruncated;
    }

    public ChatResponse setTruncated(Boolean truncated) {
        isTruncated = truncated;
        return this;
    }

    public String getFinishReason() {
        return finishReason;
    }

    public ChatResponse setFinishReason(String finishReason) {
        this.finishReason = finishReason;
        return this;
    }

    public SearchInfo getSearchInfo() {
        return searchInfo;
    }

    public ChatResponse setSearchInfo(SearchInfo searchInfo) {
        this.searchInfo = searchInfo;
        return this;
    }

    public String getResult() {
        return result;
    }

    public ChatResponse setResult(String result) {
        this.result = result;
        return this;
    }

    public Boolean getNeedClearHistory() {
        return needClearHistory;
    }

    public ChatResponse setNeedClearHistory(Boolean needClearHistory) {
        this.needClearHistory = needClearHistory;
        return this;
    }

    public Integer getFlag() {
        return flag;
    }

    public ChatResponse setFlag(Integer flag) {
        this.flag = flag;
        return this;
    }

    public ChatUsage getUsage() {
        return usage;
    }

    public ChatResponse setUsage(ChatUsage usage) {
        this.usage = usage;
        return this;
    }

    public FunctionCall getFunctionCall() {
        return functionCall;
    }

    public ChatResponse setFunctionCall(FunctionCall functionCall) {
        this.functionCall = functionCall;
        return this;
    }

    public Integer getBanRound() {
        return banRound;
    }

    public ChatResponse setBanRound(Integer banRound) {
        this.banRound = banRound;
        return this;
    }
}
