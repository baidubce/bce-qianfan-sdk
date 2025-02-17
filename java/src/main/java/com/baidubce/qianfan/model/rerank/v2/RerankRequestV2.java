package com.baidubce.qianfan.model.rerank.v2;

import com.baidubce.qianfan.model.BaseRequest;
import com.baidubce.qianfan.model.constant.ModelType;

import java.util.List;

public class RerankRequestV2 extends BaseRequest<RerankRequestV2> {
    private String query;

    private List<String> documents;

    private Integer topN;

    private String user;


    @Override
    public String getType() {
        return ModelType.RERANKER;
    }

    public String getQuery() {
        return query;
    }

    public RerankRequestV2 setQuery(String query) {
        this.query = query;
        return this;
    }

    public List<String> getDocuments() {
        return documents;
    }

    public RerankRequestV2 setDocuments(List<String> documents) {
        this.documents = documents;
        return this;
    }

    public Integer getTopN() {
        return topN;
    }

    public RerankRequestV2 setTopN(Integer topN) {
        this.topN = topN;
        return this;
    }

    public String getUser() {
        return user;
    }

    public RerankRequestV2 setUser(String user) {
        this.user = user;
        return this;
    }
}
