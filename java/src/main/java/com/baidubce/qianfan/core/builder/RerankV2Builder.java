package com.baidubce.qianfan.core.builder;

import com.baidubce.qianfan.QianfanV2;
import com.baidubce.qianfan.model.rerank.v2.RerankRequestV2;
import com.baidubce.qianfan.model.rerank.v2.RerankResponseV2;
import com.google.gson.annotations.SerializedName;

import java.util.List;

public class RerankV2Builder extends BaseBuilderV2<RerankV2Builder> {
    private String query;

    private List<String> documents;

    @SerializedName("top_n")
    private Integer topN;

    private String user;

    public RerankV2Builder() {
        super();
    }

    public RerankV2Builder(QianfanV2 qianfan) {
        super(qianfan);
    }

    public RerankV2Builder query(String query) {
        this.query = query;
        return this;
    }

    public RerankV2Builder documents(List<String> documents) {
        this.documents = documents;
        return this;
    }

    public RerankV2Builder topN(Integer topN) {
        this.topN = topN;
        return this;
    }

    public RerankV2Builder user(String user) {
        this.user = user;
        return this;
    }

    public RerankRequestV2 build() {
        return new RerankRequestV2()
                .setQuery(query)
                .setDocuments(documents)
                .setTopN(topN)
                .setUser(user)
                .setModel(super.getModel())
                .setExtraParameters(super.getExtraParameters());
    }

    public RerankResponseV2 execute() {
        return super.getQianfanV2().rerank(build());
    }
}
