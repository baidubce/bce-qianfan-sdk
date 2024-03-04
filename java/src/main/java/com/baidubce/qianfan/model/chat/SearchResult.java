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

public class SearchResult {
    /**
     * 序号
     */
    private Integer index;

    /**
     * 搜索结果URL
     */
    private String url;

    /**
     * 搜索结果标题
     */
    private String title;

    public Integer getIndex() {
        return index;
    }

    public SearchResult setIndex(Integer index) {
        this.index = index;
        return this;
    }

    public String getUrl() {
        return url;
    }

    public SearchResult setUrl(String url) {
        this.url = url;
        return this;
    }

    public String getTitle() {
        return title;
    }

    public SearchResult setTitle(String title) {
        this.title = title;
        return this;
    }
}
