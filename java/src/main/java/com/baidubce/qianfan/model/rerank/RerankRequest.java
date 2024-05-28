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

import com.baidubce.qianfan.model.BaseRequest;
import com.baidubce.qianfan.model.constant.ModelType;

import java.util.List;

public class RerankRequest extends BaseRequest<RerankRequest> {
    /**
     * 查询文本，长度不超过1600个字符，token数若超过400做截断
     */
    private String query;

    /**
     * 需要重排序的文本，说明：
     * （1）不能为空List，List的每个成员不能为空字符串
     * （2）文本数量不超过64
     * （3）每条document文本长度不超过4096个字符，token数若超过1024做截断
     */
    private List<String> documents;

    /**
     * 返回的最相关文本的数量，默认为document的数量
     */
    private Integer topN;


    @Override
    public String getType() {
        return ModelType.RERANK;
    }

    public String getQuery() {
        return query;
    }

    public RerankRequest setQuery(String query) {
        this.query = query;
        return this;
    }

    public List<String> getDocuments() {
        return documents;
    }

    public RerankRequest setDocuments(List<String> documents) {
        this.documents = documents;
        return this;
    }

    public Integer getTopN() {
        return topN;
    }

    public RerankRequest setTopN(Integer topN) {
        this.topN = topN;
        return this;
    }
}
