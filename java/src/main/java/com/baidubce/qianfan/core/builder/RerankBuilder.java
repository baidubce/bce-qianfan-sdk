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

package com.baidubce.qianfan.core.builder;

import com.baidubce.qianfan.Qianfan;
import com.baidubce.qianfan.model.rerank.RerankRequest;
import com.baidubce.qianfan.model.rerank.RerankResponse;

import java.util.List;

public class RerankBuilder extends BaseBuilder<RerankBuilder> {
    private String query;

    private List<String> documents;

    private Integer topN;

    public RerankBuilder() {
        super();
    }

    public RerankBuilder(Qianfan qianfan) {
        super(qianfan);
    }

    public RerankBuilder query(String query) {
        this.query = query;
        return this;
    }

    public RerankBuilder documents(List<String> documents) {
        this.documents = documents;
        return this;
    }

    public RerankBuilder topN(Integer topN) {
        this.topN = topN;
        return this;
    }

    public RerankRequest build() {
        return new RerankRequest()
                .setQuery(query)
                .setDocuments(documents)
                .setTopN(topN)
                .setModel(super.getModel())
                .setEndpoint(super.getEndpoint())
                .setUserId(super.getUserId())
                .setExtraParameters(super.getExtraParameters());
    }

    public RerankResponse execute() {
        return super.getQianfan().rerank(build());
    }
}
