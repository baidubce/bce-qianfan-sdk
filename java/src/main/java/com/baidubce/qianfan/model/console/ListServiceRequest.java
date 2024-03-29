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

package com.baidubce.qianfan.model.console;

import com.baidubce.qianfan.util.JsonProp;

import java.util.List;

public class ListServiceRequest {
    /**
     * 根据服务类型apiType筛选，可选值如下：
     * · chat
     * · completions
     * · embeddings
     * · text2image
     * · image2text
     */
    @JsonProp("apiTypefilter")
    private List<String> apiTypeFilter;

    public List<String> getApiTypeFilter() {
        return apiTypeFilter;
    }

    public ListServiceRequest setApiTypeFilter(List<String> apiTypeFilter) {
        this.apiTypeFilter = apiTypeFilter;
        return this;
    }
}
